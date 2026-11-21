Piedra, papel o tijera con SO-101 (Hackathon LeRobot Bilbao)

Demostración interactiva en la que un brazo robótico SO-101 reacciona a tu mano. Una cámara detecta si enseñas piedra, papel o tijera, y el robot responde con la pinza. La interfaz web está hecha con Python (Flask).

Tecnologías utilizadas
Hardware: SO-101 (Leader y Follower), ThinkPad T430, cámara USB o webcam.
Software: Python, Flask, HTML, CSS, JavaScript, LeRobot.
Detección de la mano: MediaPipe Hand Landmarker (se ejecuta en el navegador).
¿Cómo funciona?
La cámara: la página abre la webcam y detecta los puntos de tu mano.
El gesto: cuando el mismo gesto se mantiene unos instantes, el navegador lo envía al servidor.
El robot: el servidor mueve la pinza del Follower. El robot siempre elige la jugada que gana:
Tú haces	El robot hace	Con la pinza
Tijera ✌️	Piedra ✊	Se cierra
Papel ✋	Tijera ✌️	Abre y cierra varias veces
Piedra ✊	Papel ✋	Se queda abierta

La página también tiene botones para jugar sin cámara y un botón para devolver la pinza a su posición inicial.

Estructura de archivos
interfaz.py            # servidor Flask y control de la pinza
templates/index.html   # página con la cámara y la detección de la mano
static/style.css       # estilos
README.md
Cómo ejecutar el proyecto
Conectar el brazo Follower por USB-C y comprobar su puerto (Linux: /dev/ttyACM1, Windows: COM3 o similar).
Crear un entorno virtual e instalar las dependencias: uv venv y uv pip install flask lerobot.
Abrir interfaz.py y revisar la configuración del principio: SIMULACION, PUERTO_ROBOT y las posiciones de la pinza.
Ejecutar el servidor: python3 interfaz.py.
Abrir el navegador en http://localhost:5000 y permitir el acceso a la cámara.
Modo simulación

Con SIMULACION = True (valor por defecto) el brazo no se mueve y solo hace falta Flask. Sirve para probar la detección de la mano y la interfaz antes de conectar el robot. Para mover el brazo de verdad, cambia el valor a False.

Ajustes a tener en cuenta
Posiciones de la pinza: PINZA_ABIERTA y PINZA_CERRADA usan la escala 0-100 de LeRobot. Cambia los valores hasta que se vea bien con tu brazo calibrado.
Versión de LeRobot: la ruta del import y el nombre gripper.pos pueden cambiar entre versiones. Si falla, revisa la documentación de tu versión.
Internet: la primera vez, el navegador descarga el detector de manos y la fuente desde internet. Sin conexión, la detección no arranca y se puede jugar con los botones.
Iluminación: funciona mejor con buena luz y la mano a unos 50 cm de la cámara.
Equipo
Daoguo Dai Li
Zigor Pascuas Cobos
Enaitz Prieto Zubieta
Hackathon LeRobot Bilbao (Noviembre 2026)