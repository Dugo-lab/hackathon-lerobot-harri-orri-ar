from flask import Flask, render_template, request, jsonify
import atexit
import os
import socket
import subprocess
import threading
import time

app = Flask(__name__)

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
SIMULACION = False
PUERTO_WEB = 5000
HTTPS = True

# IMPORTANTE: Modo "politica" para usar el modelo entrenado
MODO = "politica" 

RESPUESTA_ROBOT = {
    "tijera": "piedra",
    "papel": "tijera",
    "piedra": "papel",
}

PUERTO_ROBOT = "/dev/ttyACM1"

# =========================================================
# MODO "directo" (por si acaso)
# =========================================================
ID_ROBOT = "mi_follower"
PINZA_ABIERTA = 90
PINZA_CERRADA = 5
PINZA_INICIAL = 50
PAUSA_PINZA = 0.8
PAUSA_TIJERA = 0.35
REPETICIONES_TIJERA = 3

# =========================================================
# MODO "politica" (modelos entrenados)
# =========================================================
INSTRUCCIONES = {
    "piedra": "Close the gripper like a rock",
    "papel": "Open the gripper like paper",
    "tijera": "Open and close the gripper like scissors",
}

PYTHON_SENSECRAFT = "/home/daoguo-dai/.local/share/SenseCraft Robotics/r/afb1f21fdf9484b9/runtime/bin/python"
CARPETA_SENSECRAFT = "/home/daoguo-dai/.local/share/SenseCraft Robotics/product-store/blobs/9f519b98f4d1c3bb253c494ca58d3581f26d0074dac5152d75cf3b662fb6807c/expanded"

PUERTO_POLITICA = 35347
ESPERA_SERVIDOR = 8
DURACION_MOVIMIENTO = 12

# TRUCO: Usamos la cámara video5 para front, y -1 para gripper (así lo ignora)
CAMARAS = (
    '{ front: { type: opencv, index_or_path: "/dev/video5", backend: 200, width: 640, height: 480, fps: 30 }, '
    'gripper: { type: opencv, index_or_path: "/dev/video0", backend: 200, width: 640, height: 480, fps: 30 }}'
)

CALIBRACION = "/home/daoguo-dai/.config/SenseCraft Robotics/backend-storage/calibration/lerobot/robots/so_follower"
BASE_MODELOS = "/home/daoguo-dai/.config/SenseCraft Robotics/backend-storage/projects/proj_7f9420fe/models"
FINAL_MODELO = "/bundle/checkpoints/last/pretrained_model"

MODELOS = {
    "piedra": BASE_MODELOS + "/cloud_local_4f01c2c4f681_artifact" + FINAL_MODELO,
    "papel": BASE_MODELOS + "/cloud_local_5f175e68d678_artifact" + FINAL_MODELO,
    "tijera": BASE_MODELOS + "/cloud_local_4f01c2c4f681_artifact" + FINAL_MODELO,
}

# =========================================================
# ESTADO
# =========================================================
robot = None
servidor_politica = None
robot_lock = threading.Lock()
rondas = 0

# =========================================================
# MODO "directo"
# =========================================================
def conectar_robot():
    global robot
    if SIMULACION or MODO != "directo":
        print("Robot no conectado desde el servidor (simulación o modo política)")
        return
    try:
        from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
    except ImportError:
        from lerobot.common.robots.so101_follower import SO101Follower, SO101FollowerConfig
    config = SO101FollowerConfig(port=PUERTO_ROBOT, id=ID_ROBOT)
    robot = SO101Follower(config)
    robot.connect()
    atexit.register(robot.disconnect)
    poner_pinza(PINZA_INICIAL)
    print("Robot conectado en", PUERTO_ROBOT)

def poner_pinza(valor, espera=PAUSA_PINZA):
    print(f"PINZA -> {valor}")
    if not SIMULACION and robot:
        robot.send_action({"gripper.pos": float(valor)})
    time.sleep(espera)

def ejecutar_directo(respuesta):
    if respuesta == "piedra":
        poner_pinza(PINZA_CERRADA)
    elif respuesta == "papel":
        poner_pinza(PINZA_ABIERTA)
    elif respuesta == "tijera":
        for _ in range(REPETICIONES_TIJERA):
            poner_pinza(PINZA_ABIERTA, PAUSA_TIJERA)
            poner_pinza(PINZA_CERRADA, PAUSA_TIJERA)

# =========================================================
# MODO "politica"
# =========================================================
def parar(proceso):
    if proceso is not None and proceso.poll() is None:
        proceso.terminate()
        try:
            proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proceso.kill()

def iniciar_servidor_politica():
    global servidor_politica
    if SIMULACION or MODO != "politica":
        return
    servidor_politica = subprocess.Popen(
        [PYTHON_SENSECRAFT, "-m", "backend.run.encoded_policy_server",
         "--host=127.0.0.1", f"--port={PUERTO_POLITICA}", "--fps=30"],
        cwd=CARPETA_SENSECRAFT)
    atexit.register(parar, servidor_politica)
    time.sleep(ESPERA_SERVIDOR)
    if servidor_politica.poll() is not None:
        raise RuntimeError("El servidor de políticas no arrancó: mira el error de arriba")
    print("Servidor de políticas listo")

def ejecutar_politica(respuesta):
    print("ROBOT:", INSTRUCCIONES[respuesta])
    if SIMULACION:
        time.sleep(2)
        return
    ruta = MODELOS[respuesta]
    if not os.path.isdir(ruta):
        raise RuntimeError(f"Todavía no hay modelo de {respuesta}")
    
    cliente = subprocess.Popen(
        [PYTHON_SENSECRAFT, "-m", "backend.run.lerobot_async_robot_client_runtime",
         "--robot.type=so100_follower", "--robot.port=" + PUERTO_ROBOT,
         "--robot.cameras=" + CAMARAS, "--robot.id=so100_follower",
         "--task=抓取积木", f"--server_address=127.0.0.1:{PUERTO_POLITICA}",
         "--policy_type=act", "--policy_device=cpu", "--client_device=cpu",
         "--actions_per_chunk=120", "--chunk_size_threshold=0.9",
         "--aggregate_fn_name=weighted_average", "--fps=30",
         "--pretrained_name_or_path=" + ruta,
         "--robot.calibration_dir=" + CALIBRACION],
        cwd=CARPETA_SENSECRAFT)
    try:
        codigo = cliente.wait(timeout=DURACION_MOVIMIENTO)
        if codigo != 0:
            raise RuntimeError("El modelo de " + respuesta + " terminó con error")
    except subprocess.TimeoutExpired:
        pass 
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
    global rondas
    datos = request.get_json(silent=True) or {}
    humano = datos.get("gesto")
    if humano not in RESPUESTA_ROBOT:
        return jsonify(ok=False, mensaje="Gesto no válido"), 400
    if not robot_lock.acquire(blocking=False):
        return jsonify(ok=False, ocupado=True, mensaje="El robot se está moviendo"), 409
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
    global rondas
    if not robot_lock.acquire(blocking=False):
        return jsonify(ok=False, ocupado=True, mensaje="El robot se está moviendo"), 409
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
    iniciar_servidor_politica()
    if HTTPS:
        try:
            import cryptography
        except ImportError:
            print("Falta 'cryptography'. Se arranca en HTTP.")
            HTTPS = False
    esquema = "https" if HTTPS else "http"
    print(f"En este equipo:   {esquema}://localhost:{PUERTO_WEB}")
    print(f"Desde la tablet:  {esquema}://{ip_local()}:{PUERTO_WEB}")
    app.run(host="0.0.0.0", port=PUERTO_WEB, debug=False, use_reloader=False,
            ssl_context="adhoc" if HTTPS else None)