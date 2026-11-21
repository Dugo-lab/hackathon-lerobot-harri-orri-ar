from flask import Flask, render_template, redirect, url_for
import random
import subprocess
import threading
import time
 
app = Flask(__name__)
 
# =========================================================
# CONFIGURACIÓN DEL ROBOT
# =========================================================
# Pon SIMULACION = True para probar la web sin el brazo conectado.
SIMULACION = True
 
# Repo de Hugging Face o ruta local de la política VLA entrenada
MODELO_VLA = "tu_usuario/tictactoe_smolvla"
 
# Color del cubo según el jugador
COLORES = {1: "yellow", 2: "green"}
 
# Argumentos fijos del comando. Revisa `lerobot-rollout --help` en tu
# versión de LeRobot: los nombres de los flags pueden cambiar.
ROBOT_ARGS = [
    "--robot.type=so101_follower",
    "--robot.port=/dev/ttyACM1",
    "--robot.id=mi_follower",
    # '--robot.cameras={...}',   # tus cámaras USB aquí
]
 
# Modo vs robot: probabilidad de que la IA haga un movimiento al azar.
# 0 = imbatible, 0.3 = se le puede ganar de vez en cuando.
PROB_ERROR = 0.3
 
# Solo un movimiento del robot a la vez
robot_lock = threading.Lock()
 
# =========================================================
# ESTADO DEL JUEGO
# =========================================================
HUMANO = 1  # Amarillo X (en modo vs robot siempre empieza el humano)
IA = 2      # Verde O
 
LINEAS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Horizontales
    [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Verticales
    [0, 4, 8], [2, 4, 6],             # Diagonales
]
 
modo = "2j"  # "2j" = dos jugadores, "ia" = jugador contra el robot
tablero = [0] * 9
jugador_actual = 1
juego_terminado = False
turno_actual = ""
mensaje_error = ""
 
 
def texto_turno(jugador):
    if jugador == 1:
        return "Turno: Jugador 1 (Amarillo X)"
    if modo == "ia":
        return "Turno: Robot (Verde O)"
    return "Turno: Jugador 2 (Verde O)"
 
 
turno_actual = texto_turno(1)
 
 
def generar_tablero():
    fichas = []
    for casilla in tablero:
        if casilla == 1:
            fichas.append('<span class="amarillo">X</span>')
        elif casilla == 2:
            fichas.append('<span class="verde">O</span>')
        else:
            fichas.append('')
    return fichas
 
 
def ganador_de(t):
    """Devuelve 1, 2 o 0 si no hay ganador en el tablero t."""
    for a, b, c in LINEAS:
        if t[a] == t[b] == t[c] != 0:
            return t[a]
    return 0
 
 
def comprobar_ganador():
    g = ganador_de(tablero)
    if g:
        if modo == "ia":
            return "¡Has ganado!" if g == HUMANO else "¡Ha ganado el robot!"
        return "¡Ha ganado el Jugador " + str(g) + "!"
    if 0 not in tablero:
        return "¡Empate!"
    return None
 
 
# =========================================================
# IA (minimax, no hace falta ninguna librería)
# =========================================================
def minimax(t, turno):
    g = ganador_de(t)
    if g == IA:
        return 1
    if g == HUMANO:
        return -1
    if 0 not in t:
        return 0
    puntuaciones = []
    for i in range(9):
        if t[i] == 0:
            t[i] = turno
            puntuaciones.append(minimax(t, HUMANO if turno == IA else IA))
            t[i] = 0
    return max(puntuaciones) if turno == IA else min(puntuaciones)
 
 
def elegir_casilla_ia():
    """Devuelve la casilla (1-9) que juega la IA."""
    libres = [i for i in range(9) if tablero[i] == 0]
    if random.random() < PROB_ERROR:
        return random.choice(libres) + 1
    mejor, mejor_p = libres[0], -2
    for i in libres:
        t = tablero[:]
        t[i] = IA
        p = minimax(t, HUMANO)
        if p > mejor_p:
            mejor, mejor_p = i, p
    return mejor + 1
 
 
# =========================================================
# ROBOT
# =========================================================
def construir_instruccion(casilla, jugador):
    """Esta frase debe ser IDÉNTICA a la usada al grabar los datasets."""
    return f"Pick the {COLORES[jugador]} cube and place it in cell {casilla}"
 
 
def mover_robot(casilla, jugador):
    """Ejecuta el movimiento en el robot. Devuelve True si fue bien."""
    instruccion = construir_instruccion(casilla, jugador)
    print("ROBOT:", instruccion)
 
    if SIMULACION:
        time.sleep(2)  # Simulamos el tiempo del brazo físico
        return True
 
    comando = [
        "lerobot-rollout",
        f"--policy.path={MODELO_VLA}",
        f"--task={instruccion}",  # comprueba el nombre exacto del flag
        *ROBOT_ARGS,
    ]
    resultado = subprocess.run(comando, check=False)
    return resultado.returncode == 0
 
 
def aplicar_jugada(casilla):
    """Mueve el robot, actualiza el tablero y cambia el turno.
    Devuelve False si el robot falló (la jugada se deshace)."""
    global turno_actual, jugador_actual, juego_terminado, mensaje_error
    indice = casilla - 1
 
    tablero[indice] = jugador_actual
    if not mover_robot(casilla, jugador_actual):
        tablero[indice] = 0
        mensaje_error = "Error del robot, repite la jugada"
        print("ROBOT: fallo en el movimiento")
        return False
 
    mensaje_error = ""
    resultado = comprobar_ganador()
    if resultado:
        turno_actual = resultado
        juego_terminado = True
    else:
        jugador_actual = 2 if jugador_actual == 1 else 1
        turno_actual = texto_turno(jugador_actual)
    return True
 
 
def turno_ia():
    aplicar_jugada(elegir_casilla_ia())
 
 
# =========================================================
# RUTAS
# =========================================================
@app.route('/')
def home():
    fichas = generar_tablero()
    return render_template('index.html', turno=turno_actual, modo=modo,
                           error=mensaje_error,
                           c1=fichas[0], c2=fichas[1], c3=fichas[2],
                           c4=fichas[3], c5=fichas[4], c6=fichas[5],
                           c7=fichas[6], c8=fichas[7], c9=fichas[8])
 
 
@app.route('/jugar/<int:casilla>')
def jugar(casilla):
    if casilla < 1 or casilla > 9:
        return redirect(url_for('home'))
 
    # Si el robot está ocupado, ignoramos el clic
    if not robot_lock.acquire(blocking=False):
        return redirect(url_for('home'))
 
    try:
        if juego_terminado:
            return redirect(url_for('home'))
 
        # Si el robot falló en su turno anterior, lo reintenta
        if modo == "ia" and jugador_actual == IA:
            turno_ia()
            return redirect(url_for('home'))
 
        if tablero[casilla - 1] != 0:
            return redirect(url_for('home'))
 
        # Jugada del humano (el robot coloca el cubo)
        if aplicar_jugada(casilla):
            # En modo vs robot, responde la IA
            if modo == "ia" and not juego_terminado and jugador_actual == IA:
                turno_ia()
    finally:
        robot_lock.release()
 
    return redirect(url_for('home'))
 
 
@app.route('/modo/<nuevo_modo>')
def cambiar_modo(nuevo_modo):
    global modo
    if nuevo_modo in ("2j", "ia") and not robot_lock.locked():
        modo = nuevo_modo
        reiniciar_estado()
    return redirect(url_for('home'))
 
 
def reiniciar_estado():
    global tablero, turno_actual, jugador_actual, juego_terminado, mensaje_error
    tablero = [0] * 9
    jugador_actual = 1
    turno_actual = texto_turno(1)
    juego_terminado = False
    mensaje_error = ""
 
 
@app.route('/reiniciar')
def reiniciar():
    if not robot_lock.locked():
        reiniciar_estado()
    return redirect(url_for('home'))
 
 
if __name__ == '__main__':
    print("Servidor iniciado en http://localhost:5000")
    # use_reloader=False evita que el script arranque dos veces y se pelee por el puerto serie
    app.run(debug=True, use_reloader=False, port=5000)
 