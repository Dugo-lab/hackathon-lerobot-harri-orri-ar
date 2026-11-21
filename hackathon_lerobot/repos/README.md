# 🤖 Tres en Raya con SO-101 (Hackathon LeRobot Bilbao)

Este proyecto es una demostración interactiva de robótica de imitación. Un brazo robótico SO-101 aprende a jugar al Tres en Raya (Tic-Tac-Toe) mediante teleoperación y aprendizaje por imitación, conectado a una interfaz web en tiempo real.

## 🛠️ Tecnologías utilizadas
*   **Hardware:** SO-101 (Leader y Follower), ThinkPad T430, cámaras USB.
*   **Software:** Ubuntu, Python, Flask, SenseCraft Robotics.
*   **Entrenamiento:** Cloud GPU (RTX 2080 Ti / RTX 3090).

## 🚀 ¿Cómo funciona?
1.  **El robot inicia:** El brazo robótico mueve una ficha amarilla a la casilla central (estrategia de apertura).
2.  **El humano responde:** Un operador humano coloca una ficha verde en el tablero físico.
3.  **Interfaz interactiva:** Una interfaz web local (en Flask) muestra el estado del tablero en tiempo real, recargándose automáticamente cada 2 segundos.

## 🧠 Flujo de entrenamiento
*   Se grabaron 20 episodios teleoperando el brazo para que aprendiera a coger el bloque amarillo y dejarlo en el centro.
*   El modelo (política ACT) fue entrenado en la nube para suplir la falta de GPU local.

## 🏃‍♂️ Cómo ejecutar nuestro proyecto (Reproducibilidad)
Para replicar nuestro entorno y ejecutar el modelo:
1. Conectar los brazos: Leader en `/dev/ttyACM0` y Follower en `/dev/ttyACM1`.
2. Crear un entorno virtual e instalar Flask: `uv venv` y `uv pip install flask`.
3. Ejecutar el servidor web: `python3 interfaz.py`.
4. Abrir el navegador en `http://localhost:5000`.
5. Lanzar el modelo entrenado en el robot real usando LeRobot.

## 👥 Equipo
*   Daoguo Dai Li
*   Zigor Pascuas Cobos
*   Enaitz Prieto Zubieta

## 🏆 Hackathon LeRobot Bilbao (Noviembre 2026)