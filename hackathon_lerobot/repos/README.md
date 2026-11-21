# Tres en Raya con SO-101 (Hackathon LeRobot Bilbao)

Este proyecto es una demostración interactiva de robótica de imitación. Un brazo robótico SO-101 actúa como el "brazo ejecutor" de una partida de Tres en Raya (Tic-Tac-Toe), coordinado a través de una interfaz web desarrollada en Python (Flask).

## Tecnologías utilizadas
*   **Hardware:** SO-101 (Leader y Follower), ThinkPad T430, cámaras USB.
*   **Software:** Ubuntu, Python, Flask, HTML, CSS, SenseCraft Robotics.
*   **Entrenamiento:** Cloud GPU.

## ¿Cómo funciona el juego?
1.  **La interfaz web:** Dos jugadores interactúan con un tablero digital en el navegador.
2.  **El turno:** Cuando un jugador hace clic en una casilla, la web envía una orden al robot.
3.  **El robot:** El brazo físico coge un cubo de una zona de recogida y lo deposita en la casilla física correspondiente del tablero en la mesa.

## Flujo de entrenamiento
*   Para que el robot sepa moverse a cada casilla, se grabaron múltiples datasets (20 episodios por casilla).
*   Los modelos (política ACT) fueron entrenados en la nube para suplir la falta de GPU local.

##  Cómo ejecutar nuestro proyecto (Reproducibilidad)
1. Conectar los brazos: Leader en `/dev/ttyACM0` y Follower en `/dev/ttyACM1`.
2. Crear un entorno virtual e instalar Flask: `uv venv` y `uv pip install flask`.
3. Ejecutar el servidor web: `python3 interfaz.py`.
4. Abrir el navegador en `http://localhost:5000`.

## Equipo
*   Daoguo Dai Li
*   Zigor Pascuas Cobos
*   Enaitz Prieto Zubieta

## Hackathon LeRobot Bilbao (Noviembre 2026)