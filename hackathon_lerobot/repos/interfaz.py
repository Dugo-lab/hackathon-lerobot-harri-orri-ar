from flask import Flask, render_template, request, jsonify
import atexit
import os
import shlex
import subprocess
import threading
import time
 
app = Flask(__name__)
 
# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
# Pon SIMULACION = True para probar la web sin el brazo conectado.
SIMULACION = True
 
# "directo"  -> mueve la pinza con valores fijos (versión sin entrenamiento, sirve para probar)
# "politica" -> lanza el modelo entrenado de cada dataset (versión final)
MODO = "directo"
 
# El robot siempre elige lo que le gana a tu gesto:
#   tú tijera -> robot piedra | tú papel -> robot tijera | tú piedra -> robot papel
RESPUESTA_ROBOT = {
    "tijera": "piedra",
    "papel": "tijera",
    "piedra": "papel",
}
 
# =========================================================
# MODO "directo" (sin entrenamiento)
# =========================================================
PUERTO_ROBOT = "/dev/ttyACM1"   # Windows: "COM3"
ID_ROBOT = "mi_follower"
PINZA_ABIERTA = 90
PINZA_CERRADA = 5
PINZA_INICIAL = 50
PAUSA_PINZA = 0.8
PAUSA_TIJERA = 0.35
REPETICIONES_TIJERA = 3
 
# =========================================================
# MODO "politica" (con los modelos entrenados)
# =========================================================
# Instrucción de cada dataset: tiene que ser IDÉNTICA a la usada al grabarlo.
INSTRUCCIONES = {
    "piedra": "Close the gripper like a rock",
    "papel": "Open the gripper like paper",
    "tijera": "Open and close the gripper like scissors",
}
 
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# PEGAR AQUÍ: el comando que lanza cada modelo entrenado.
# Escríbelo tal como lo ejecutas en la terminal, en una sola línea
# (o con "\" al final de cada línea). Sustituye el texto entre comillas.
# El modelo de PIEDRA es el que cierra la pinza, etc.
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
COMANDOS = {
    "piedra": "PEGAR AQUÍ EL COMANDO DEL MODELO DE PIEDRA",
    "papel": "PEGAR AQUÍ EL COMANDO DEL MODELO DE PAPEL",
    "tijera": "PEGAR AQUÍ EL COMANDO DEL MODELO DE TIJERA",
}
 
# Si el modelo tarda más de esto en terminar (segundos), se corta
TIEMPO_MAXIMO = 120
 
# =========================================================
# ESTADO
# =========================================================
robot = None
robot_lock = threading.Lock()  # solo un movimiento a la vez
rondas = 0
 
 
# =========================================================
# MODO "directo"
# =========================================================
def conectar_robot():
    """Conecta con el SO-101 Follower. Solo en modo directo:
    en modo política, el comando de cada modelo abre el puerto por su cuenta."""
    global robot
    if SIMULACION or MODO != "directo":
        print("Robot no conectado desde el servidor (simulación o modo política)")
        return
 
    # La ruta del import cambia según la versión de LeRobot
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
    if not SIMULACION:
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
def ejecutar_politica(respuesta):
    """Lanza el comando del modelo entrenado para esa respuesta."""
    texto = COMANDOS[respuesta]
    if texto.startswith("PEGAR AQU"):
        raise RuntimeError(f"Falta pegar el comando del modelo de {respuesta} en COMANDOS")
 
    print("ROBOT:", INSTRUCCIONES[respuesta])
    if SIMULACION:
        time.sleep(2)  # Simulamos el tiempo del brazo físico
        return
 
    texto = texto.replace("\\\n", " ")
    comando = shlex.split(texto, posix=(os.name != "nt"))
    resultado = subprocess.run(comando, check=False, timeout=TIEMPO_MAXIMO)
    if resultado.returncode != 0:
        raise RuntimeError("El modelo de " + respuesta + " terminó con error")
 
 
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
 
    # Si el robot sigue moviéndose, ignoramos el gesto
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
        # En modo política no hay conexión abierta, así que solo se reinicia el marcador
        if MODO == "directo":
            poner_pinza(PINZA_INICIAL)
        rondas = 0
        return jsonify(ok=True, rondas=rondas)
    except Exception as error:
        print("ROBOT: fallo al reiniciar:", error)
        return jsonify(ok=False, mensaje="No se pudo reiniciar la pinza"), 500
    finally:
        robot_lock.release()
 
 
if __name__ == "__main__":
    conectar_robot()
    print("Servidor iniciado en http://localhost:5000")
    # use_reloader=False evita que el script arranque dos veces y se pelee por el puerto serie
    app.run(debug=True, use_reloader=False, port=5000)
 