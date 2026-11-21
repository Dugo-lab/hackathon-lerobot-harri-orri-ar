# Piedra, papel o tijera con SO-101 (Hackathon LeRobot Bilbao)

Demostración interactiva en la que un brazo robótico SO-101 reacciona a tu mano. Una cámara detecta si enseñas piedra, papel o tijera, y el robot responde con la pinza. La interfaz web está hecha con Python (Flask) y funciona tanto en el portátil como en una tablet.

## Tecnologías utilizadas

- **Hardware:** SO-101 (Leader y Follower), ThinkPad T430, cámara USB o webcam, tablet (opcional).
- **Software:** Python, Flask, HTML, CSS, JavaScript, LeRobot.
- **Detección de la mano:** MediaPipe Hand Landmarker (se ejecuta en el navegador).
- **Entrenamiento de los modelos:** SenseCraft Robotics / LeRobot (política ACT).

## ¿Cómo funciona?

1. **La cámara:** la página abre la cámara y detecta los puntos de tu mano.
2. **El gesto:** cuando el mismo gesto se mantiene unos instantes, el navegador lo envía al servidor.
3. **El robot:** el servidor mueve el Follower. El robot siempre elige la jugada que gana:

| Tú haces | El robot hace | Con la pinza |
|---|---|---|
| Tijera ✌️ | Piedra ✊ | Se cierra |
| Papel ✋ | Tijera ✌️ | Abre y cierra varias veces |
| Piedra ✊ | Papel ✋ | Se queda abierta |

La página también tiene botones grandes para jugar sin cámara y un botón para devolver la pinza a su posición inicial.

## Estructura de archivos

```
interfaz.py            # servidor Flask y control del robot
templates/index.html   # página con la cámara y la detección de la mano
static/style.css       # estilos (portátil y tablet)
README.md
```

La carpeta `templates/` y la carpeta `static/` tienen que llamarse exactamente así: Flask las busca por su nombre.

## Cómo ejecutar el proyecto

1. Conecta el brazo Follower por USB-C y comprueba su puerto (Linux: `/dev/ttyACM1`, Windows: `COM3` o similar).
2. Entra en la carpeta del proyecto (la que contiene `interfaz.py`).
3. Crea un entorno virtual, actívalo e instala las dependencias.

   **Windows (PowerShell):**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install flask cryptography
   ```
   Si PowerShell dice que la ejecución de scripts está deshabilitada, ejecuta antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

   **Linux:**
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install flask cryptography
   ```

   Para mover el brazo de verdad, LeRobot también tiene que estar instalado en ese entorno.
4. Abre `interfaz.py` y revisa la configuración del principio: `SIMULACION`, `MODO`, `PUERTO_ROBOT`, `PUERTO_WEB` y `HTTPS`.
5. Arranca el servidor: `python interfaz.py` (en Linux, `python3 interfaz.py`). La terminal muestra las direcciones para abrir la web.
6. Abre la dirección en el navegador y permite el acceso a la cámara.

> La web hay que abrirla siempre a través del servidor Flask. No sirve abrir `index.html` con Live Server o haciendo doble clic: es una plantilla de Flask y sin el servidor no carga ni el CSS ni los botones.

## Usarlo desde la tablet

El servidor escucha en toda la red, así que la tablet puede usar la web mientras el robot sigue conectado por USB al portátil. La tablet hace de pantalla y de cámara.

1. Conecta la tablet y el portátil a la **misma wifi**.
2. Arranca el servidor. La terminal muestra algo así:
   ```
   En este equipo:   https://localhost:5000
   Desde la tablet:  https://192.168.x.x:5000  (misma wifi)
   ```
3. Escribe la segunda dirección en el navegador de la tablet.
4. El navegador avisará de que la conexión no es privada, porque el certificado es autofirmado. Pulsa "Avanzado" y "Continuar". Después permite la cámara.

Cosas a tener en cuenta:

- **HTTPS:** los navegadores solo dejan usar la cámara desde `localhost` o con `https://`. Por eso `HTTPS = True` (necesita el paquete `cryptography`). Si falta, el servidor arranca en HTTP y la cámara de la tablet no funcionará, pero los botones sí.
- **Firewall de Windows:** la primera vez puede preguntar si permites Python en redes privadas. Acepta.
- **Wifi con aislamiento:** algunas redes (hackathones, colegios) impiden que los dispositivos se vean entre sí. Si la tablet no conecta, usa el punto de acceso del móvil para los dos equipos.
- **Modo debug desactivado:** abierto a la red, el modo debug permitiría ejecutar código a cualquiera. Por eso, al cambiar el HTML o el CSS, hay que reiniciar el servidor y refrescar el navegador con `Ctrl + Shift + R`.

## Modos de funcionamiento

### Simulación

Con `SIMULACION = True` (valor por defecto) el brazo no se mueve y solo hace falta Flask. Sirve para probar la detección de la mano y la interfaz antes de conectar el robot. Para mover el brazo de verdad, cambia el valor a `False`.

### Modo `directo` (sin entrenamiento)

Con `MODO = "directo"` el servidor se conecta al SO-101 y mueve la pinza con valores fijos (`PINZA_ABIERTA`, `PINZA_CERRADA`, `PINZA_INICIAL`). Sirve para probar todo el sistema sin modelos entrenados.

### Modo `politica` (con los modelos entrenados)

Con `MODO = "politica"` cada respuesta del robot la ejecuta un modelo entrenado distinto. Hay **4 datasets**, uno por cada hueco del diccionario `COMANDOS` de `interfaz.py`:

| Dataset | Qué hace el robot |
|---|---|
| `piedra` | Cierra la pinza |
| `papel` | Abre la pinza |
| `tijera` | Abre y cierra la pinza |
| `nada` | No hace nada (se queda quieto) |

Para cada uno hay que rellenar dos cosas:

- **`INSTRUCCIONES`:** la frase del dataset. Tiene que ser idéntica a la usada al grabarlo.
- **`COMANDOS`:** el comando que lanza el modelo entrenado, en una sola línea. Mientras ponga `PEGAR AQUÍ...`, el servidor avisa de que falta ese comando.

Ejemplo de comando para un hueco:

```python
"nada": '''lerobot-rollout --strategy.type=base --policy.path=C:/ruta/pretrained_model --robot.type=so101_follower --robot.port=COM3 --robot.id=mi_follower --robot.cameras="{ up: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30} }" --task="Do nothing" --duration=10''',
```

- `--policy.path`: carpeta `pretrained_model` del modelo entrenado (con `/` en lugar de `\`).
- `--robot.cameras`: debe ser igual a la configuración de cámaras con la que se grabó el dataset.
- `--task`: la misma frase que en `INSTRUCCIONES`.
- `--duration`: segundos que se ejecuta el modelo. Tiene que ser menor que `TIEMPO_MAXIMO` (120 s por defecto), o el servidor cortará el modelo y dará error.

Prueba siempre el comando a mano en la terminal antes de pegarlo en `interfaz.py`.

> Por ahora la web solo envía piedra, papel y tijera. El hueco `nada` está preparado en el servidor (si recibe ese gesto, el robot se queda quieto), pero la interfaz todavía no tiene un botón ni una detección que lo active.

## Ajustes a tener en cuenta

- **Posiciones de la pinza:** `PINZA_ABIERTA` y `PINZA_CERRADA` usan la escala 0-100 de LeRobot. Cambia los valores hasta que se vea bien con tu brazo calibrado.
- **Versión de LeRobot:** la ruta del import, el nombre `gripper.pos` y el comando de inferencia pueden cambiar entre versiones. En versiones recientes se usa `lerobot-rollout`; en la 0.5.1 y anteriores, `lerobot-record`. Si falla, revisa la documentación de tu versión.
- **Internet:** la primera vez, el navegador descarga el detector de manos y la fuente desde internet. Sin conexión, la detección no arranca y se puede jugar con los botones. En la tablet también hace falta conexión.
- **Iluminación:** funciona mejor con buena luz y la mano a unos 50 cm de la cámara.

## Equipo

- Daoguo Dai Li
- Zigor Pascuas Cobos
- Enaitz Prieto Zubieta

Hackathon LeRobot Bilbao (Noviembre 2026)
