#  Tres en Raya con SO-101 (Hackathon LeRobot Bilbao)

Este proyecto es una demostración interactiva de robótica de imitación. Un brazo robótico SO-101 aprende a jugar al Tres en Raya (Tic-Tac-Toe) mediante teleoperación y aprendizaje por imitación.

##  Tecnologías utilizadas
*   **Hardware:** SO-101 (Leader y Follower), ThinkPad T430, cámaras USB.
*   **Software:** Ubuntu 22.04, Python, SenseCraft Robotics, Flask (para la interfaz web).
*   **Entrenamiento:** Cloud GPU (RTX 2080 Ti).

##  ¿Cómo funciona?
1.  **El robot inicia la partida:** El brazo robótico (follower) mueve una ficha amarilla a la casilla central (estrategia de apertura).
2.  **El humano responde:** Un operador humano (o el juez) coloca una ficha verde en el tablero físico.
3.  **Interfaz interactiva:** Una interfaz web local (en Flask) muestra el estado del tablero actualizado en tiempo real.

##  Flujo de entrenamiento
*   Se grabaron 20 episodios teleoperando el brazo para que aprendiera a coger el bloque amarillo y dejarlo en el centro.
*   El modelo (política ACT) fue entrenado en la nube para suplir la falta de GPU local.

##  Cómo ejecutar nuestro proyecto (Reproducibilidad)
Para replicar nuestro entorno y ejecutar el modelo:
1. Conectar los brazos: Leader en `/dev/ttyACM0` y Follower en `/dev/ttyACM1`.
2. Activar el entorno y lanzar la interfaz web: `python3 interfaz.py`.
3. Descargar el modelo entrenado desde Hugging Face.
4. Ejecutar el modelo en el robot real usando LeRobot.

##  Equipo
*   Daoguo Dai Li
*   Zigor Pascuas Cobos
*   Enaitz Prieto Zubieta

##  Hackathon LeRobot Bilbao (Noviembre 2026)
