Piedra, papel o tijera contra un brazo SO-101

Proyecto desarrollado en el Hackathon LeRobot Bilbao (noviembre de 2026). Una cámara detecta el gesto de la mano de una persona (piedra, papel o tijera) y un brazo robótico SO-101 responde con la pinza, eligiendo siempre la jugada que gana. La interfaz es una página web servida con Flask que se puede usar desde el propio portátil o desde una tablet.

Funcionamiento

El sistema se reparte en dos partes. En el navegador, la página abre la cámara y detecta los puntos de la mano con MediaPipe Hand Landmarker. Un clasificador sencillo decide si el gesto es piedra, papel o tijera según qué dedos están extendidos, y cuando el mismo gesto se mantiene durante varios fotogramas seguidos se envía al servidor. En el servidor, Flask recibe el gesto, calcula la respuesta del robot y mueve el brazo. Mientras el brazo se mueve, el servidor rechaza nuevas peticiones para evitar que se solapen los movimientos.

El robot siempre juega la opción que gana. Si el humano saca tijera, el robot responde con piedra y cierra la pinza. Si saca papel, el robot responde con tijera y abre y cierra la pinza varias veces. Si saca piedra, el robot responde con papel y deja la pinza abierta. La página incluye además botones para jugar sin cámara y un botón para devolver la pinza a su posición inicial.

Tecnologías

El hardware utilizado es un brazo SO-101 (Leader y Follower), un portátil con Linux, una cámara web o USB y, de forma opcional, una tablet. El servidor está escrito en Python 3 con Flask, y la interfaz en HTML, CSS y JavaScript sin necesidad de compilación. La detección de la mano usa MediaPipe Tasks Vision y se ejecuta en el navegador. El robot se controla con LeRobot, y los modelos del modo política se entrenaron con SenseCraft Robotics y LeRobot usando la política ACT.

Estructura del repositorio

El archivo interfaz.py contiene el servidor Flask y el control del robot. La página con la cámara y la detección de la mano está en templates/index.html, y sus estilos para portátil y tablet en static/style.css. Las dependencias de Python se listan en requirements.txt. Las carpetas templates y static deben mantener esos nombres, porque Flask las busca por defecto.

Requisitos

Hace falta Python 3.10 o superior y un navegador moderno con acceso a la cámara. La primera vez que se abre la página se necesita conexión a internet para descargar el detector de manos y la tipografía. Para mover el brazo de verdad, además, LeRobot debe estar instalado en el mismo entorno, el Follower conectado por USB y su calibración hecha.

Instalación

Primero hay que clonar el repositorio con git clone <url-del-repositorio> y entrar en la carpeta. Después se crea un entorno virtual con python3 -m venv .venv, se activa con source .venv/bin/activate y se instalan las dependencias con pip install -r requirements.txt. En Windows el entorno se activa con .venv\Scripts\Activate.ps1, y si PowerShell bloquea la ejecución de scripts se puede permitir solo para esa sesión con Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass. Si se va a controlar el robot, hay que instalar también LeRobot siguiendo su documentación oficial, ya que no se incluye en requirements.txt.

Ejecución

Antes de arrancar conviene revisar la configuración que aparece al principio de interfaz.py, descrita en la sección siguiente. El servidor se arranca con python3 interfaz.py, y la terminal muestra dos direcciones: una para abrir la web en el propio equipo, del tipo https://localhost:5000, y otra para abrirla desde la tablet, del tipo https://192.168.x.x:5000. Se abre la dirección en el navegador y se concede el permiso de cámara.

La web debe abrirse siempre a través del servidor. No funciona abriendo index.html con doble clic ni con extensiones del tipo Live Server, porque es una plantilla de Flask y necesita que el servidor la renderice.

Configuración

Los parámetros principales están al inicio de interfaz.py. SIMULACION indica si el brazo se mueve o no: con True solo se imprime la acción que se ejecutaría, y es el valor por defecto. MODO puede ser "directo" o "politica", que se explican más abajo. PUERTO_WEB es el puerto en el que escucha el servidor, 5000 por defecto, y HTTPS activa un certificado autofirmado, necesario para usar la cámara desde otro dispositivo. Por último, PINZA_ABIERTA, PINZA_CERRADA y PINZA_INICIAL definen las posiciones de la pinza en el modo directo, en la escala de 0 a 100 de LeRobot.

Algunas rutas dependen del equipo y se pueden cambiar con variables de entorno sin tocar el código. ROBOT_PORT es el puerto serie del Follower y vale /dev/ttyACM0 por defecto. ROBOT_ID es el identificador del robot en la calibración y vale mi_follower. LEROBOT_CALIBRACION y LEROBOT_MODELOS apuntan a la carpeta de calibración y a la carpeta de modelos entrenados, y por defecto usan el almacenamiento de SenseCraft. Por ejemplo, para usar otro puerto se puede ejecutar ROBOT_PORT=/dev/ttyACM1 python3 interfaz.py. Como el puerto puede cambiar al reconectar el cable USB, en Linux se puede comprobar cuál está activo con ls /dev/ttyACM*.

Modos de funcionamiento
Simulación

Con SIMULACION = True el brazo no se mueve y solo hace falta Flask. Es útil para probar la detección de la mano y la interfaz sin tener el robot conectado.

Modo directo

Con SIMULACION = False y MODO = "directo", el servidor se conecta al SO-101 desde Python y mueve la pinza con los valores fijos definidos en la configuración. No requiere modelos entrenados, por lo que es la forma más sencilla de comprobar todo el sistema con el robot real. Si el archivo de calibración no existe, el servidor lo avisa al arrancar e indica el comando para generarlo, que tiene la forma lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=mi_follower. Este es el modo que se utilizó en la demostración final.

Modo política (experimental)

Con MODO = "politica", cada respuesta del robot la ejecuta un modelo ACT entrenado con un dataset distinto, lanzado mediante lerobot-rollout. Hay un dataset por gesto: piedra, con la instrucción "Close the gripper like a rock", y papel, con la instrucción "Open the gripper like paper", ya tienen modelo entrenado. El de tijera, con la instrucción "Open and close the gripper like scissors", está pendiente. Los modelos se localizan a partir de LEROBOT_MODELOS y del diccionario ARTIFACTS de interfaz.py, que asocia cada gesto con la carpeta del artifact entrenado, de modo que para añadir el modelo de tijera basta con incluir su entrada en ese diccionario.

Este modo no funciona de forma fiable en el estado actual del proyecto. El servidor construye y lanza el comando de lerobot-rollout, pero la ejecución del modelo falla y el brazo no se mueve. No se llegó a depurar la causa durante el hackathon, y el resto de la aplicación no depende de este modo.

Para retomarlo, lo más práctico es copiar el comando que imprime el servidor en la línea que empieza por [lerobot-rollout] comando:, lanzarlo directamente en una terminal y revisar el error. Conviene comprobar que los flags existen en la versión de LeRobot instalada con lerobot-rollout --help, porque entre versiones han cambiado el comando de inferencia y algunos argumentos. También hay que verificar que los nombres de las cámaras, front y gripper, coinciden con los del dataset de entrenamiento, que los índices de /dev/video* y el puerto del robot son los actuales, y que ningún otro proceso, como la aplicación de SenseCraft, tiene abierto el puerto serie.

Uso desde una tablet

El servidor escucha en toda la red local, de modo que la tablet puede hacer de pantalla y de cámara mientras el robot sigue conectado por USB al portátil. Para ello, la tablet y el portátil deben estar en la misma red wifi. Se arranca el servidor y en la tablet se escribe la dirección que la terminal muestra como "Desde la tablet". El navegador avisará de que la conexión no es privada, porque el certificado es autofirmado; hay que elegir las opciones avanzadas y continuar, y después conceder el permiso de cámara.

Los navegadores solo permiten usar la cámara desde localhost o con HTTPS, así que si falta el paquete cryptography el servidor arranca en HTTP: los botones siguen funcionando, pero la cámara de la tablet no. Algunas redes, como las de eventos o centros educativos, impiden que los dispositivos se vean entre sí, y si la tablet no conecta una solución es usar el punto de acceso del móvil para ambos equipos. En Windows, la primera vez puede aparecer un aviso del cortafuegos para permitir Python en redes privadas. Por último, el modo debug de Flask está desactivado a propósito, porque abierto a la red permitiría ejecutar código de forma remota, así que tras modificar el HTML o el CSS hay que reiniciar el servidor y recargar el navegador sin caché con Ctrl + Shift + R.

Consejos de uso

La detección funciona mejor con buena iluminación y la mano a unos 50 cm de la cámara. Hay que mantener el gesto quieto un instante hasta que se envíe, y para repetir el mismo gesto primero hay que bajar la mano. Si el robot no responde, la propia página muestra el mensaje de error devuelto por el servidor, y los detalles aparecen en la terminal.

Autores

Proyecto realizado por Daoguo Dai Li, Zigor Pascuas Cobos y Enaitz Prieto Zubieta.