"""Piedra, papel o tijera contra un brazo robótico SO-101.
 
Servidor Flask que recibe el gesto detectado en el navegador y hace que el
brazo responda con la jugada ganadora. Tiene tres formas de funcionar:
 
* Simulación: no se toca el robot, solo se imprime lo que haría.
* Modo "directo": se mueve la pinza con valores fijos desde Python.
* Modo "politica": se lanza un modelo ACT entrenado con lerobot-rollout
  (experimental, ver README).
 
La configuración está al principio del archivo. Las rutas dependientes del
equipo se pueden cambiar con variables de entorno sin tocar el código.
"""
 
import atexit
import os
import socket
import subprocess
import threading
import time
from pathlib import Path
 
from flask import Flask, jsonify, render_template, request
 
app = Flask(__name__)
 
# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
SIMULACION = True        # True: el brazo no se mueve
MODO = "directo"         # "directo" o "politica"
PUERTO_WEB = 5000
HTTPS = True             # necesario para usar la cámara desde otro dispositivo
 
PUERTO_ROBOT = os.environ.get("ROBOT_PORT", "/dev/ttyACM0")
ID_ROBOT = os.environ.get("ROBOT_ID", "mi_follower")
 
# El robot siempre juega la opción que gana al gesto del humano.
RESPUESTA_ROBOT = {
    "tijera": "piedra",
    "papel": "tijera",
    "piedra": "papel",
}
 
# =========================================================
# MODO "directo"
# =========================================================
# Posiciones de la pinza en la escala 0-100 de LeRobot.
PINZA_ABIERTA = 90
PINZA_CERRADA = 5
PINZA_INICIAL = 50
 
PAUSA_PINZA = 0.8          # segundos de espera tras cada movimiento
PAUSA_TIJERA = 0.35        # pausa entre aperturas y cierres de la tijera
REPETICIONES_TIJERA = 3
 
# =========================================================
# MODO "politica" (lerobot-rollout)
# =========================================================
# Con la política ACT el texto de --task es solo una etiqueta: lo que decide
# el movimiento es el modelo que se carga (uno por gesto).
INSTRUCCIONES = {
    "piedra": "Close the gripper like a rock",
    "papel": "Open the gripper like paper",
    "tijera": "Open and close the gripper like scissors",
}
 
DURACION_MOVIMIENTO = 10   # segundos que se ejecuta cada modelo
 
# Los nombres de las cámaras deben coincidir con los usados al grabar el dataset.
CAMARAS = (
    '{ front: { type: opencv, index_or_path: "/dev/video5", backend: 200, width: 640, height: 480, fps: 30 }, '
    'gripper: { type: opencv, index_or_path: "/dev/video0", backend: 200, width: 640, height: 480, fps: 30 }}'
)
 
_SENSECRAFT = Path.home() / ".config" / "SenseCraft Robotics" / "backend-storage"
 
CALIBRACION = os.environ.get(
    "LEROBOT_CALIBRACION",
    str(_SENSECRAFT / "calibration" / "lerobot" / "robots" / "so_follower"),
)
BASE_MODELOS = Path(os.environ.get(
    "LEROBOT_MODELOS",
    str(_SENSECRAFT / "projects" / "proj_7f9420fe" / "models"),
))
FINAL_MODELO = Path("bundle") / "checkpoints" / "last" / "pretrained_model"
 
# Carpeta del artifact entrenado para cada gesto. El de tijera está pendiente.
ARTIFACTS = {
    "piedra": "cloud_local_4f01c2c4f681_artifact",
    "papel": "cloud_local_5f175e68d678_artifact",
}
 
# =========================================================
# ESTADO
# =========================================================
robot = None
robot_lock = threading.Lock()
rondas = 0
 
 
# =========================================================
# MODO "directo"
# =========================================================
def conectar_robot():
    """Conecta con el brazo (solo en modo directo y sin simulación)."""
    global robot
    if SIMULACION or MODO != "directo":
        print("Robot no conectado desde el servidor (simulación o modo política)")
        return
 
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
 
    ruta_calib = os.path.join(CALIBRACION, ID_ROBOT + ".json")
    if not os.path.exists(ruta_calib):
        print("=" * 60)
        print("ATENCIÓN: no existe el archivo de calibración:")
        print("  ", ruta_calib)
        print("Calibra primero a mano con:")
        print(f"  lerobot-calibrate --robot.type=so101_follower "
              f"--robot.port={PUERTO_ROBOT} --robot.id={ID_ROBOT}")
        print("=" * 60)
 
    config = SO101FollowerConfig(port=PUERTO_ROBOT, id=ID_ROBOT)
    robot = SO101Follower(config)
    robot.connect()
    atexit.register(robot.disconnect)
    poner_pinza(PINZA_INICIAL)
    print("Robot conectado en", PUERTO_ROBOT)
 
 
def poner_pinza(valor, espera=PAUSA_PINZA):
    """Mueve la pinza a una posición y espera a que llegue."""
    print(f"PINZA -> {valor}")
    if not SIMULACION and robot:
        robot.send_action({"gripper.pos": float(valor)})
    time.sleep(espera)
 
 
def ejecutar_directo(respuesta):
    """Representa el gesto del robot moviendo la pinza con valores fijos."""
    if respuesta == "piedra":
        poner_pinza(PINZA_CERRADA)
    elif respuesta == "papel":
        poner_pinza(PINZA_ABIERTA)
    elif respuesta == "tijera":
        for _ in range(REPETICIONES_TIJERA):
            poner_pinza(PINZA_ABIERTA, PAUSA_TIJERA)
            poner_pinza(PINZA_CERRADA, PAUSA_TIJERA)
 
 
# =========================================================
# MODO "politica" (lerobot-rollout)
# =========================================================
def parar(proceso):
    """Termina un proceso hijo, con kill si no responde a tiempo."""
    if proceso is not None and proceso.poll() is None:
        proceso.terminate()
        try:
            proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proceso.kill()
 
 
def ruta_modelo(gesto):
    """Devuelve la carpeta del modelo de un gesto, o None si no está definido."""
    artifact = ARTIFACTS.get(gesto)
    if artifact is None:
        return None
    return str(BASE_MODELOS / artifact / FINAL_MODELO)
 
 
def ejecutar_politica(respuesta):
    """Lanza el modelo entrenado del gesto con lerobot-rollout."""
    print("ROBOT:", INSTRUCCIONES[respuesta])
    if SIMULACION:
        time.sleep(2)
        return
 
    ruta = ruta_modelo(respuesta)
    if ruta is None or not os.path.isdir(ruta):
        raise RuntimeError(f"Todavía no hay modelo de {respuesta}")
 
    # Estrategia "base": ejecución autónoma sin grabar datos.
    comando = [
        "lerobot-rollout",
        "--strategy.type=base",
        "--policy.path=" + ruta,
        "--robot.type=so101_follower",
        "--robot.port=" + PUERTO_ROBOT,
        "--robot.id=" + ID_ROBOT,
        "--robot.calibration_dir=" + CALIBRACION,
        "--robot.cameras=" + CAMARAS,
        "--task=" + INSTRUCCIONES[respuesta],
        "--duration=" + str(DURACION_MOVIMIENTO),
        "--display_data=false",
    ]
    print("[lerobot-rollout] comando:", " ".join(comando))
 
    cliente = subprocess.Popen(
        comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
 
    try:
        salida, _ = cliente.communicate(timeout=DURACION_MOVIMIENTO + 30)
        if salida:
            print("[lerobot-rollout]")
            print(salida)
        if cliente.returncode != 0:
            raise RuntimeError(
                "lerobot-rollout terminó con código " + str(cliente.returncode))
    except subprocess.TimeoutExpired:
        print("[lerobot-rollout] timeout, matando")
        parar(cliente)
        raise RuntimeError("lerobot-rollout no terminó a tiempo")
    finally:
        parar(cliente)
 
 
def ejecutar_respuesta(respuesta):
    if MODO == "politica":
        ejecutar_politica(respuesta)
    else:
        ejecutar_directo(respuesta)
 
 
# =========================================================
# RUTAS
# =========================================================
@app.route("/")
def home():
    return render_template("index.html", simulacion=SIMULACION, rondas=rondas)
 
 
@app.route("/gesto", methods=["POST"])
def gesto():
    """Recibe el gesto del humano y hace que el robot responda."""
    global rondas
    datos = request.get_json(silent=True) or {}
    humano = datos.get("gesto")
    if humano not in RESPUESTA_ROBOT:
        return jsonify(ok=False, mensaje="Gesto no válido"), 400
    if not robot_lock.acquire(blocking=False):
        return jsonify(ok=False, ocupado=True,
                       mensaje="El robot se está moviendo"), 409
    try:
        respuesta = RESPUESTA_ROBOT[humano]
        print(f"TÚ: {humano}  ->  ROBOT: {respuesta}")
        ejecutar_respuesta(respuesta)
        rondas += 1
        return jsonify(ok=True, humano=humano, robot=respuesta, rondas=rondas)
    except Exception as error:
        print("ROBOT: fallo en el movimiento:", error)
        return jsonify(ok=False, mensaje="Error del robot: " + str(error)), 500
    finally:
        robot_lock.release()
 
 
@app.route("/reiniciar", methods=["POST"])
def reiniciar():
    """Devuelve la pinza a su posición inicial y pone el marcador a cero."""
    global rondas
    if not robot_lock.acquire(blocking=False):
        return jsonify(ok=False, ocupado=True,
                       mensaje="El robot se está moviendo"), 409
    try:
        if MODO == "directo" and robot:
            poner_pinza(PINZA_INICIAL)
        rondas = 0
        return jsonify(ok=True, rondas=rondas)
    except Exception as error:
        print("ROBOT: fallo al reiniciar:", error)
        return jsonify(ok=False, mensaje="No se pudo reiniciar la pinza"), 500
    finally:
        robot_lock.release()
 
 
def ip_local():
    """IP del equipo en la red local, para abrir la web desde otro dispositivo."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()
 
 
if __name__ == "__main__":
    conectar_robot()
    if HTTPS:
        try:
            import cryptography  # noqa: F401
        except ImportError:
            print("Falta 'cryptography'. Se arranca en HTTP.")
            HTTPS = False
    esquema = "https" if HTTPS else "http"
    print(f"En este equipo:   {esquema}://localhost:{PUERTO_WEB}")
    print(f"Desde la tablet:  {esquema}://{ip_local()}:{PUERTO_WEB}")
    app.run(host="0.0.0.0", port=PUERTO_WEB, debug=False, use_reloader=False,
            ssl_context="adhoc" if HTTPS else None)
 