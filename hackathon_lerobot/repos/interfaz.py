from flask import Flask
import time

app = Flask(__name__)

# 0 = vacío, 1 = Humano (O), 2 = Robot (X)
tablero = [0, 0, 0, 0, 0, 0, 0, 0, 0]
turno_actual = "Esperando al robot..."

# El HTML como un String gigante (igual que si lo escribieras en un archivo)
html_base = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="2">
    <title>Tres en Raya</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <header>
        <h1>🤖 Tres en Raya 🟢</h1>
        <h2>__TURNO__</h2>
    </header>
    <main>
        <div class="tablero">
            __CASILLAS__
        </div>
    </main>
    <footer>
        <p>Hackathon LeRobot Bilbao</p>
    </footer>
</body>
</html>
"""

@app.route('/')
def home():
    # 1. Generamos las casillas del tablero con un bucle normal de Python
    casillas_html = ""
    for casilla in tablero:
        if casilla == 1:
            casillas_html += '<article class="celda"><span class="verde">O</span></article>'
        elif casilla == 2:
            casillas_html += '<article class="celda"><span class="amarillo">X</span></article>'
        else:
            casillas_html += '<article class="celda"></article>'

    # 2. Reemplazamos las palabras clave en el HTML base
    html_final = html_base.replace("__TURNO__", turno_actual)
    html_final = html_final.replace("__CASILLAS__", casillas_html)

    # 3. Devolvemos el HTML al navegador
    return html_final

def jugar_robot():
    global turno_actual
    turno_actual = "El robot está moviendo..."
    print("El robot está moviendo...")
    
    time.sleep(5) 
    
    tablero[4] = 2 
    turno_actual = "Turno del humano"
    print("El robot ha terminado.")

if __name__ == '__main__':
    jugar_robot()
    print("Servidor iniciado en http://localhost:5000")
    app.run(debug=True, port=5000)