from flask import Flask, render_template, redirect, url_for
import time
# import subprocess # Descomenta esto mañana para llamar a LeRobot

app = Flask(__name__)

# Variables globales
tablero = [0, 0, 0, 0, 0, 0, 0, 0, 0]
turno_actual = "Turno: Jugador 1 (Amarillo X)"
jugador_actual = 1
juego_terminado = False

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

def comprobar_ganador():
    # Combinaciones ganadoras (índices 0-8)
    lineas = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # Horizontales
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # Verticales
        [0, 4, 8], [2, 4, 6]             # Diagonales
    ]
    for linea in lineas:
        if tablero[linea[0]] == tablero[linea[1]] == tablero[linea[2]] != 0:
            return "¡Ha ganado el Jugador " + str(tablero[linea[0]]) + "!"
    if 0 not in tablero:
        return "¡Empate!"
    return None

@app.route('/')
def home():
    fichas = generar_tablero()
    return render_template('index.html', turno=turno_actual,
                           c1=fichas[0], c2=fichas[1], c3=fichas[2],
                           c4=fichas[3], c5=fichas[4], c6=fichas[5],
                           c7=fichas[6], c8=fichas[7], c9=fichas[8])

@app.route('/jugar/<int:casilla>')
def jugar(casilla):
    global turno_actual, jugador_actual, juego_terminado
    indice = casilla - 1

    if not juego_terminado and tablero[indice] == 0:
        tablero[indice] = jugador_actual
        
        # =========================================================
        # AQUÍ VAN LOS COMANDOS DEL ROBOT REAL (LeRobot)
        # =========================================================
        if casilla == 1:
            print("ROBOT: Moviendo a Casilla 1")
            # subprocess.run(["lerobot-rollout", "--policy.path=MODELO_1", ...])
        elif casilla == 2:
            print("ROBOT: Moviendo a Casilla 2")
            # subprocess.run(["lerobot-rollout", "--policy.path=MODELO_2", ...])
        elif casilla == 3:
            print("ROBOT: Moviendo a Casilla 3")
            # subprocess.run(["lerobot-rollout", "--policy.path=MODELO_3", ...])
        elif casilla == 4:
            print("ROBOT: Moviendo a Casilla 4")
            # subprocess.run(["lerobot-rollout", "--policy.path=MODELO_4", ...])
        elif casilla == 5:
            print("ROBOT: Moviendo a Casilla 5")
            # subprocess.run(["lerobot-rollout", "--policy.path=MODELO_5", ...])
        elif casilla == 6:
            print("ROBOT: Moviendo a Casilla 6")
            # subprocess.run(["lerobot-rollout", "--policy.path=MODELO_6", ...])
        elif casilla == 7:
            print("ROBOT: Moviendo a Casilla 7")
            # subprocess.run(["lerobot-rollout", "--policy.path=MODELO_7", ...])
        elif casilla == 8:
            print("ROBOT: Moviendo a Casilla 8")
            # subprocess.run(["lerobot-rollout", "--policy.path=MODELO_8", ...])
        elif casilla == 9:
            print("ROBOT: Moviendo a Casilla 9")
            # subprocess.run(["lerobot-rollout", "--policy.path=MODELO_9", ...])

        time.sleep(2) # Simulamos el tiempo del brazo físico
        # =========================================================

        # Comprobar si alguien ha ganado
        resultado = comprobar_ganador()
        if resultado:
            turno_actual = resultado
            juego_terminado = True
        else:
            # Cambiamos el turno
            if jugador_actual == 1:
                jugador_actual = 2
                turno_actual = "Turno: Jugador 2 (Verde O)"
            else:
                jugador_actual = 1
                turno_actual = "Turno: Jugador 1 (Amarillo X)"

    return redirect(url_for('home'))

@app.route('/reiniciar')
def reiniciar():
    global tablero, turno_actual, jugador_actual, juego_terminado
    tablero = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    turno_actual = "Turno: Jugador 1 (Amarillo X)"
    jugador_actual = 1
    juego_terminado = False
    return redirect(url_for('home'))

if __name__ == '__main__':
    print("Servidor iniciado en http://localhost:5000")
    app.run(debug=True, port=5000)