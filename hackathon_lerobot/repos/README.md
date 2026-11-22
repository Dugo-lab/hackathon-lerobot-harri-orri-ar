Piedra, papel o tijera contra un brazo SO-101

Proyecto desarrollado en el Hackathon LeRobot Bilbao (noviembre de 2026). Una cámara detecta el gesto de la mano de una persona (piedra, papel o tijera) y un brazo robótico SO-101 responde con la pinza, eligiendo siempre la jugada que gana. La interfaz es una página web servida con Flask que se puede usar desde el propio portátil o desde una tablet.

Funcionamiento

El sistema se reparte en dos partes:

Navegador. La página abre la cámara y detecta los puntos de la mano con MediaPipe Hand Landmarker. Un clasificador sencillo decide si el gesto es piedra, papel o tijera según qué dedos están extendidos. Cuando el mismo gesto se mantiene durante varios fotogramas seguidos, se envía al servidor.
Servidor. Flask recibe el gesto, calcula la respuesta del robot y mueve el brazo. Mientras el brazo se mueve rechaza nuevas peticiones para evitar solapar movimientos.

El robot responde así:

Humano	Robot	Movimiento de la pinza
Tijera	Piedra	Se cierra
Papel	Tijera	Se abre y se cierra varias veces
Piedra	Papel	Se abre

La página incluye también botones para jugar sin cámara y un botón para devolver la pinza a su posición inicial.

Tecnologías
Hardware: brazo SO-101 (Leader y Follower), portátil Linux, cámara web o USB y, opcionalmente, una tablet.
Backend: Python 3 y Flask.
Frontend: HTML, CSS y JavaScript sin dependencias de compilación.
Detección de la mano: MediaPipe Tasks Vision (Hand Landmarker), ejecutado en el navegador.
Control del robot: LeRobot.
Entrenamiento de los modelos: SenseCraft Robotics y LeRobot, con la política ACT.
Estructura del repositorio
.
├── interfaz.py            Servidor Flask y control del robot
├── templates/
│   └── index.html         Página con la cámara y la detección de la mano
├── static/
│   └── style.css          Estilos para portátil y tablet
├── requirements.txt       Dependencias de Python
└── README.md

Las carpetas templates/ y static/ deben mantener esos nombres, porque Flask las busca por defecto.

Requisitos
Python 3.10 o superior.
Un navegador moderno con acceso a la cámara.
Conexión a internet la primera vez, para descargar el detector de manos y la tipografía.
Para mover el brazo de verdad: LeRobot instalado en el mismo entorno, el Follower conectado por USB y su calibración hecha.
Instalación
bash
git clone <url-del-repositorio>
cd <carpeta-del-repositorio>

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

En Windows, el entorno se activa con .venv\Scripts\Activate.ps1. Si PowerShell bloquea la ejecución de scripts, se puede permitir solo para esa sesión con Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass.

Si se va a controlar el robot, hay que instalar también LeRobot siguiendo su documentación oficial, ya que no se incluye en requirements.txt.

Ejecución
Revisa la configuración que aparece al principio de interfaz.py (ver la sección siguiente).
Arranca el servidor:
bash
python3 interfaz.py
La terminal muestra las direcciones disponibles:
En este equipo:   https://localhost:5000
Desde la tablet:  https://192.168.x.x:5000
Abre la dirección en el navegador y concede el permiso de cámara.

La web debe abrirse siempre a través del servidor. No funciona abriendo index.html con doble clic ni con extensiones tipo Live Server, porque es una plantilla de Flask y necesita que el servidor la renderice.

Configuración

Los parámetros principales están al inicio de interfaz.py:

Parámetro	Descripción
SIMULACION	Si es True, el brazo no se mueve y solo se imprime la acción. Es el valor por defecto.
MODO	"directo" o "politica" (ver más abajo).
PUERTO_WEB	Puerto en el que escucha el servidor. Por defecto 5000.
HTTPS	Activa HTTPS con un certificado autofirmado. Necesario para la cámara desde otro dispositivo.
PINZA_ABIERTA, PINZA_CERRADA, PINZA_INICIAL	Posiciones de la pinza en el modo directo, en la escala 0-100 de LeRobot.

Algunas rutas dependen del equipo y se pueden cambiar con variables de entorno, sin editar el código:

Variable	Uso	Valor por defecto
ROBOT_PORT	Puerto serie del Follower	/dev/ttyACM0
ROBOT_ID	Identificador del robot en la calibración	mi_follower
LEROBOT_CALIBRACION	Carpeta con el archivo de calibración	Almacenamiento de SenseCraft
LEROBOT_MODELOS	Carpeta que contiene los modelos entrenados	Almacenamiento de SenseCraft

Ejemplo:

bash
ROBOT_PORT=/dev/ttyACM1 python3 interfaz.py

El puerto del robot puede cambiar al reconectar el cable USB. Se puede comprobar con ls /dev/ttyACM* en Linux.

Modos de funcionamiento
Simulación

Con SIMULACION = True el brazo no se mueve y solo hace falta Flask. Es útil para probar la detección de la mano y la interfaz sin tener el robot conectado.

Modo directo

Con SIMULACION = False y MODO = "directo", el servidor se conecta al SO-101 desde Python y mueve la pinza con los valores fijos definidos en la configuración. No requiere modelos entrenados, por lo que es la forma más sencilla de comprobar todo el sistema con el robot real. Si el archivo de calibración no existe, el servidor lo avisa al arrancar e indica el comando para generarlo:

bash
lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=mi_follower

Este es el modo que se utilizó en la demostración final.

Modo política (experimental)

Con MODO = "politica", cada respuesta del robot la ejecuta un modelo ACT entrenado con un dataset distinto, lanzado mediante lerobot-rollout. Los datasets definidos son:

Gesto	Instrucción del dataset	Modelo
Piedra	Close the gripper like a rock	Entrenado
Papel	Open the gripper like paper	Entrenado
Tijera	Open and close the gripper like scissors	Pendiente

Los modelos se localizan a partir de LEROBOT_MODELOS y del diccionario ARTIFACTS de interfaz.py, que asocia cada gesto con la carpeta del artifact entrenado. Para añadir el modelo de tijera basta con incluir su entrada en ese diccionario.

Estado actual: este modo no funciona de forma fiable. El servidor construye y lanza el comando de lerobot-rollout, pero la ejecución del modelo falla y el brazo no se mueve. No se ha llegado a depurar la causa durante el hackathon. El resto de la aplicación no depende de este modo.

Para retomarlo, lo más práctico es lanzar el comando que imprime el servidor (línea [lerobot-rollout] comando:) directamente en una terminal y revisar el error. Conviene comprobar:

Que los flags existen en la versión de LeRobot instalada (lerobot-rollout --help). Entre versiones han cambiado el comando de inferencia y algunos argumentos.
Que los nombres de las cámaras (front y gripper) coinciden con los del dataset de entrenamiento.
Que los índices de las cámaras (/dev/video*) y el puerto del robot son los actuales.
Que ningún otro proceso, como la aplicación de SenseCraft, tiene abierto el puerto serie.
Uso desde una tablet

El servidor escucha en toda la red local, de modo que la tablet puede hacer de pantalla y de cámara mientras el robot sigue conectado por USB al portátil.

Conecta la tablet y el portátil a la misma red wifi.
Arranca el servidor y escribe en la tablet la dirección que aparece como "Desde la tablet".
El navegador avisará de que la conexión no es privada, porque el certificado es autofirmado. Hay que elegir las opciones avanzadas y continuar. Después se concede el permiso de cámara.

Algunas consideraciones:

HTTPS. Los navegadores solo permiten usar la cámara desde localhost o con HTTPS. Si falta el paquete cryptography, el servidor arranca en HTTP: los botones siguen funcionando, pero la cámara de la tablet no.
Aislamiento de red. Algunas redes (eventos, centros educativos) impiden que los dispositivos se vean entre sí. Si la tablet no conecta, una solución es usar el punto de acceso del móvil para ambos equipos.
Cortafuegos. En Windows, la primera vez puede aparecer un aviso para permitir Python en redes privadas.
Cambios en la interfaz. El modo debug de Flask está desactivado a propósito, porque abierto a la red permitiría ejecutar código de forma remota. Tras modificar el HTML o el CSS hay que reiniciar el servidor y recargar el navegador sin caché (Ctrl + Shift + R).
Consejos de uso
La detección funciona mejor con buena iluminación y la mano a unos 50 cm de la cámara.
Hay que mantener el gesto quieto un instante hasta que se envíe. Para repetir el mismo gesto, primero hay que bajar la mano.
Si el robot no responde, la propia página muestra el mensaje de error devuelto por el servidor, y los detalles aparecen en la terminal.
Autores
Daoguo Dai Li
Zigor Pascuas Cobos
Enaitz Prieto Zubieta