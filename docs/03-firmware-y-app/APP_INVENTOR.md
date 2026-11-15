# App Android con MIT App Inventor

Guía para construir la app que habla el protocolo de `docs/03-firmware-y-app/PROTOCOLO.md` con los módulos `DUELO-A` y `DUELO-B`.

**El protocolo manda.** Si esta guía dice algo distinto a `docs/03-firmware-y-app/PROTOCOLO.md`, gana el protocolo y hay que corregir la guía.

**Convención:** *(verificar en App Inventor)* marca un bloque, propiedad o nombre de pantalla que no puedo confirmar de memoria. Búscalo en el editor antes de usarlo y corrige esta guía si difiere. Los bloques se citan con los nombres en inglés que muestra App Inventor por defecto.

---

## 0. Requisitos y limitación de iPhone

- **Necesitas un celular Android.** Con iPhone esta app no funciona. El ESP32 se comunica por Bluetooth clásico (SPP), y iOS no permite a apps de terceros usar ese perfil. App Inventor, además, solo genera apps Android. Si el equipo solo tiene iPhone, hay que conseguir un Android prestado para las pruebas.
- Cuenta de Google para entrar a App Inventor, un PC con navegador y, opcional, un cable USB.
- Instala **MIT AI2 Companion** en el celular desde Play Store. Es la app que ejecuta tu proyecto mientras programas: en App Inventor, menú **Connect → AI Companion**, y escanea el código QR desde la app del celular.
- **El emulador no sirve**: no tiene Bluetooth real. Prueba siempre en el celular.
- El módulo debe estar encendido, con el firmware cargado (ver `docs/03-firmware-y-app/BRINGUP.md`, paso 1) y **sin** el puente de MAINT, para que arranque en modo Bluetooth.

---

## 1. Emparejar el ESP32 con el celular

Emparejar lo hace el **sistema Android**, no la app. Se hace una vez por celular y por módulo.

1. Enciende el módulo y espera 10 s.
2. Abre **Ajustes → Bluetooth**. La ruta cambia según la marca (en algunos celulares: Conexiones → Bluetooth, o Dispositivos conectados → Vincular nuevo dispositivo).
3. Toca **Buscar** o **Vincular**. Debe aparecer `DUELO-A` o `DUELO-B`. El nombre viene de `DEVICE_NAME` en `include/config.h`.
4. Toca el nombre. Si pide PIN, escribe **1234**. Si no pide nada, acepta.
5. Confirma que dice **Vinculado**. "Disponible" no basta.
6. Repite con el otro módulo si este celular va a disparar contra él o a marcar en él.

Notas:

- El ESP32 acepta **un solo teléfono a la vez**. Si otro celular está conectado, el tuyo no entra. Hay que pulsar **Desconectar** antes.
- Al abrir la app por primera vez, Android pide permiso de Bluetooth o de "Dispositivos cercanos". Acepta. Si no lo pidió, ve a Ajustes → Apps → tu app → Permisos.

---

## 2. Quién se conecta a quién

La app se conecta a **un módulo a la vez**. El módulo depende de la acción:

| Acción | Tu celular se conecta a... | Por qué |
|---|---|---|
| Disparar contra el tablero del rival | el módulo del rival | ese módulo apunta al tablero del rival |
| TEST, CAL y PING de tu propio módulo | tu módulo | calibras y pruebas tu tablero |
| MARK HIT / MARK MISS de un disparo recibido | tu módulo | el dueño del tablero marca el resultado |

Ejemplo: el Jugador 1 tiene `DUELO-A` en su tablero y el Jugador 2 tiene `DUELO-B`. El Jugador 1 dispara a B: su celular se conecta a `DUELO-B`, envía `(x,y)`, recibe `OK (x,y)` y se desconecta. Luego el Jugador 2 conecta su celular a `DUELO-B` y marca MARK HIT o MARK MISS.

---

## 3. Cómo se ve la pantalla

Una sola pantalla. Este dibujo es orientativo; el diseño final es tuyo (ver sección 8).

```
+------------------------------------------+
|  [ Título de tu app ]                    |
|  [ Elegir módulo              v ]        |
|  [ Conectar ]     Estado: Sin conexión   |
|                                          |
|  X: 10  [=======o==================]     |
|  Y:  4  [===o======================]     |
|                                          |
|  [        DISPARAR        ]              |
|  [ TEST ]  [ STOP ]                      |
|  [ MARK HIT ] [ MARK MISS ] [ PING ]     |
|                                          |
|  Comando libre: [______________] [Enviar]|
|  Registro:                               |
|  > (10,4)                                |
|  < OK (10,4)                             |
+------------------------------------------+
```

El cuadro "Comando libre" es opcional, pero lo recomiendo: sirve para las pruebas de error del plan de pruebas (sección 7) sin tocar código.

---

## 4. Componentes (pestaña Designer)

Crea un proyecto nuevo en App Inventor (Projects → Start new project). Elige nombres de componentes **propios** (ver sección 8). Los nombres de la tabla son sugerencias.

| Paleta | Componente | Nombre sugerido | Propiedades que importan |
|---|---|---|---|
| Layout | VerticalArrangement | — | contenedor de la pantalla |
| User Interface | Label | `lblTitulo` | texto con el nombre de tu app |
| User Interface | ListPicker | `lpModulos` | `Text` = "Elegir módulo"; `ElementsFromString` vacío |
| User Interface | Button | `btnConectar` | `Text` = "Conectar" |
| User Interface | Label | `lblEstado` | `Text` = "Sin conexión" |
| User Interface | Slider | `sldX` | mínimo 1, máximo 20, posición inicial 10 (verificar en App Inventor los nombres exactos: `MinValue`, `MaxValue`, `ThumbPosition`) |
| User Interface | Label | `lblX` | muestra el valor de X |
| User Interface | Slider | `sldY` | igual que `sldX` |
| User Interface | Label | `lblY` | muestra el valor de Y |
| User Interface | Button | `btnDisparar` | `Text` = "DISPARAR" |
| User Interface | Button | `btnTest` | `Text` = "TEST" |
| User Interface | Button | `btnStop` | `Text` = "STOP"; color que se vea como parada |
| User Interface | Button | `btnMarcaAcierto` | `Text` = "MARK HIT" |
| User Interface | Button | `btnMarcaFallo` | `Text` = "MARK MISS" |
| User Interface | Button | `btnPing` | `Text` = "PING" (recomendado, para comprobar la conexión) |
| User Interface | TextBox | `txtComando` | comando libre para pruebas |
| User Interface | Button | `btnEnviarLibre` | `Text` = "Enviar" |
| User Interface | TextBox | `txtRegistro` | `MultiLine` activado; `ReadOnly` activado (verificar en App Inventor) |
| Connectivity | BluetoothClient | `BluetoothClient1` | `Enabled` activado; `DelimiterByte` = 10, que es el salto de línea (verificar en App Inventor) |
| Sensors | Clock | `relojLector` | `TimerInterval` = 150 (ms); `TimerEnabled` activado |
| User Interface | Notifier | `Notifier1` | avisos emergentes |

Notas:

- Si el editor no tiene `MinValue` o `MaxValue`, busca "Minimum" o "Maximum" (verificar en App Inventor).
- Los sliders no dan números enteros. Por eso el código redondea (bloque `round`).
- La cuadrícula de 20 × 20 también sirve, pero requiere 40 botones o un mapa tocable. Para una primera versión, dos sliders son lo más simple que funciona.

---

## 5. Lógica (bloques)

Los bloques reales se arrastran en el editor. Este pseudocódigo muestra qué hace cada uno. Las ramas se resuelven con `if` y `else`.

### 5.1 Variables globales

```
initialize global modo to ""        # "" = nada en curso; "disparo" = esperando OK (x,y); "test" = esperando TEST DONE
```

### 5.2 Procedimiento para enviar

```
to enviar(texto):
    call BluetoothClient1.SendText( join(texto, <salto de línea>) )   # el \n es obligatorio (verificar en App Inventor: bloque de salto de línea en Texto)
    set txtRegistro.Text to join(txtRegistro.Text, "> ", texto, <salto de línea>)
```

El protocolo exige **una línea por mensaje** terminada en `\n`. Sin el salto, el módulo no ejecuta el comando.

### 5.3 Pantalla y selector

```
when Screen1.Initialize:
    set lblEstado.Text to "Elige un módulo y pulsa Conectar"
    set modo to ""

when lpModulos.BeforePicking:                  # refresca la lista cada vez que la abres (verificar en App Inventor)
    set lpModulos.Elements to BluetoothClient1.AddressesAndNames   # (verificar en App Inventor)
```

`AddressesAndNames` devuelve los dispositivos emparejados. Así ves `DUELO-A` sin escribir su dirección.

### 5.4 Conectar y desconectar

```
when btnConectar.Click:
    if BluetoothClient1.IsConnected:
        call BluetoothClient1.Disconnect
        set btnConectar.Text to "Conectar"
        set lblEstado.Text to "Desconectado"
    else:
        if lpModulos.Selection está vacío:
            call Notifier1.ShowAlert("Elige primero un módulo")
        else:
            ok = call BluetoothClient1.Connect( address = lpModulos.Selection )   # verificar en App Inventor: si pide solo la dirección (17 caracteres) o admite el texto completo
            if ok:
                set btnConectar.Text to "Desconectar"
                set lblEstado.Text to join("Conectado a ", lpModulos.Selection)
                call enviar("PING")
            else:
                set lblEstado.Text to "No conectó: revisa el emparejamiento y que el módulo esté encendido"
```

### 5.5 Sliders

```
when sldX.PositionChanged (thumbPosition):      # verificar en App Inventor el nombre del evento
    set lblX.Text to join("X: ", round(thumbPosition))

when sldY.PositionChanged (thumbPosition):
    set lblY.Text to join("Y: ", round(thumbPosition))
```

### 5.6 Disparar, TEST, STOP y marcas

```
when btnDisparar.Click:
    if no BluetoothClient1.IsConnected:
        call Notifier1.ShowAlert("Conéctate primero")
    else if modo <> "":
        call Notifier1.ShowAlert("Espera: hay una orden en curso")
    else:
        x = round(sldX.ThumbPosition)
        y = round(sldY.ThumbPosition)
        set modo to "disparo"
        set lblEstado.Text to join("Disparando (", x, ",", y, ")...")
        call enviar( join("(", x, ",", y, ")") )

when btnTest.Click:
    if no BluetoothClient1.IsConnected or modo <> "":
        call Notifier1.ShowAlert("Conéctate y espera a que termine la orden anterior")
    else:
        set modo to "test"
        set lblEstado.Text to "Test de 5 posiciones en curso (unos 25 s)..."
        call enviar("TEST")

when btnStop.Click:
    call enviar("STOP")          # STOP se atiende siempre, incluso durante un disparo

when btnMarcaAcierto.Click:
    call enviar("MARK HIT")

when btnMarcaFallo.Click:
    call enviar("MARK MISS")

when btnPing.Click:
    call enviar("PING")

when btnEnviarLibre.Click:       # sin comprobaciones a propósito: sirve para probar errores
    call enviar(txtComando.Text)
```

### 5.7 Leer las respuestas (el reloj)

Un `Clock` mira cada 150 ms si llegó algo del módulo y lo procesa.

```
when relojLector.Timer:
    if no BluetoothClient1.IsConnected and btnConectar.Text = "Desconectar":
        set btnConectar.Text to "Conectar"
        set lblEstado.Text to "Conexión perdida"
        set modo to ""
    while BluetoothClient1.BytesAvailableToReceive > 0:        # (verificar en App Inventor: propiedad)
        linea = call BluetoothClient1.ReceiveTextUntilDelimiter        # (verificar en App Inventor) lee hasta el DelimiterByte (10)
        call procesar(linea)
```

Si la app se congela un instante al leer, o si una línea llega cortada, usa la versión con buffer (5.9).

### 5.8 Interpretar cada línea

```
to procesar(linea):
    linea = trim(linea)                                  # quita espacios y \r (verificar en App Inventor)
    if linea = "": stop
    añadir join("< ", linea, salto) a txtRegistro

    if linea empieza con "PONG":          set lblEstado.Text to join("Listo: ", linea)
    else if linea empieza con "OK (":     if modo = "disparo": set modo to ""; set lblEstado.Text to join("Disparo terminado ", linea)
    else if linea = "TEST START":         set lblEstado.Text to "Test en curso..."
    else if linea = "TEST DONE":          set modo to ""; set lblEstado.Text to "Test completo"
    else if linea empieza con "TEST ABORT": set modo to ""; set lblEstado.Text to "Test abortado"
    else if linea empieza con "ERR":      set modo to ""; set lblEstado.Text to join("Error: ", linea)
    else if linea = "OK STOP":            set modo to ""; set lblEstado.Text to "Detenido"
    else if linea empieza con "OK MARK":  set lblEstado.Text to "Marca guardada"
    # las líneas "CAL ..." solo quedan en el registro
```

Esta versión es simple y tiene un límite: un `ERR` que llegue durante un TEST pone `modo` a vacío. Para la entrega basta, pero anótalo si lo ves.

### 5.9 Versión con buffer (si las líneas llegan cortadas)

Guarda lo recibido en una variable hasta que aparezca un salto de línea.

```
initialize global buffer to ""

when relojLector.Timer:
    (las comprobaciones de desconexión de 5.7)
    while BluetoothClient1.BytesAvailableToReceive > 0:
        buffer = join(buffer, call BluetoothClient1.ReceiveText(BluetoothClient1.BytesAvailableToReceive))   # (verificar en App Inventor)
    while buffer contiene salto de línea:                                 # (verificar en App Inventor: bloque "contains" de Texto)
        linea = texto antes del salto                                     # (verificar en App Inventor: "split at first" o "segment")
        buffer = texto después del salto
        call procesar(linea)
```

---

## 6. Qué responde el módulo y qué hace la app

Las respuestas completas están en `docs/03-firmware-y-app/PROTOCOLO.md`. Esta tabla resume lo que la app debe reconocer.

| Línea que llega | Qué hace la app |
|---|---|
| `PONG DUELO-A 0.1.0` | estado "Listo" con nombre y versión |
| `OK (x,y)` | termina el disparo que estaba en curso |
| `ERR FORMAT`, `ERR RANGE`, `ERR LIMIT`, `ERR BUSY`, `ERR STOP`, `ERR EMPTY`, `ERR TOOLONG`, `ERR UNKNOWN` | muestra el error en el estado y en el registro. No reintentar solo |
| `TEST START`, cinco `OK (x,y)`, `TEST DONE` | estado de test; el registro muestra las 5 posiciones en orden |
| `TEST ABORT` seguido de un `ERR ...` | test abortado y motivo |
| `OK STOP` | detenido. Llega después de `ERR STOP` si había un disparo |
| `OK MARK` | marca guardada. **Tarda unos 2 s**: el módulo enciende el LED antes de responder |
| `CAL x y h panTrim tiltTrim` | solo al registro |

Dos detalles de tiempo:

- Un disparo tarda más de 1,5 s, porque el láser se queda encendido ese tiempo antes del `OK`. Mientras tanto, la app no debe enviar otra orden. El módulo respondería `ERR BUSY`. La app ya avisa "Espera" si pulsas DISPARAR con una orden en curso, pero el comando libre no tiene esa protección, y eso es lo que se prueba en el caso 8.
- El TEST tarda unos 20 a 30 s.

---

## 7. Plan de pruebas

Haz las pruebas **en este orden**. Cada una depende de la anterior. "Banco" significa el módulo montado con su tablero.

| # | Prueba | Pasos | Resultado esperado |
|---|---|---|---|
| 1 | Emparejamiento | Ajustes → Bluetooth → vincular `DUELO-A` | Dice "Vinculado". Aparece en el selector de la app |
| 2 | Conexión y PING | Elegir `DUELO-A` → Conectar | El botón cambia a "Desconectar". El registro muestra `PONG DUELO-A 0.1.0` en menos de 1 s |
| 3 | Conectar sin elegir | Pulsar Conectar sin elegir módulo | Aviso "Elige primero un módulo". La app no se cierra |
| 4 | Disparo normal | X = 1, Y = 1 → DISPARAR | Estado "Disparando (1,1)...". Luego `OK (1,1)`. En el banco, el láser enciende unos 1,5 s |
| 5 | Disparo en el extremo | X = 20, Y = 20 → DISPARAR | `OK (20,20)`. El rayo cae en la celda lejana del tablero |
| 6 | Línea mal escrita | Comando libre `(3,4` → Enviar | `ERR FORMAT`. El estado muestra el error. El brazo no se mueve |
| 7 | Fuera de rango | Comando libre `(21,5)` → Enviar | `ERR RANGE` |
| 8 | Orden durante un disparo | Pulsa DISPARAR y, con el estado "Disparando" visible, envía `PING` en el comando libre. Si el disparo ya terminó, repite | `ERR BUSY` para el PING. El disparo termina con `OK (x,y)` |
| 9 | STOP a mitad de un disparo | DISPARAR; pulsar STOP enseguida | El láser se apaga al instante. Llegan `ERR STOP` (del disparo) y `OK STOP`. Estado "Detenido" |
| 10 | TEST completo | Pulsar TEST | Registro: `TEST START`, cinco `OK` en el orden (1,1), (20,1), (20,20), (1,20), (11,11), luego `TEST DONE`. Tarda unos 20-30 s |
| 11 | Marcas | MARK HIT, luego MARK MISS | Cada una responde `OK MARK`. HIT enciende el LED unos 2 s antes de la respuesta. MISS no enciende el LED |
| 12 | Módulo apagado | Con la app conectada, apagar el módulo | En 2 s o menos, la app muestra "Conexión perdida" y el botón vuelve a "Conectar". La app no se congela |
| 13 | Reconexión | Encender el módulo; pulsar Conectar | Vuelve a dar `PONG` |
| 14 | Dos teléfonos | Con un celular conectado, intentar conectar otro al mismo módulo | El segundo no entra. Es lo esperado: un teléfono por módulo |
| 15 | Calibración por el comando libre | Comando libre `CAL SHOW` | Responde `CAL x y h panTrim tiltTrim` con los valores guardados |

Si una prueba falla, anótala con la hora, la línea del registro y la captura de pantalla. Son parte de la evidencia.

---

## 8. Cómo hacer que la app sea original

Las apps de los compañeros no deben parecerse a la tuya. Estas decisiones son tuyas, y conviene anotarlas en el informe con el porqué.

- **Nombre y icono propios.** Pon el nombre en `Screen1.AppName` y un icono que tú hayas elegido (`Screen1.Icon`).
- **Paleta de colores propia.** No dejes los colores por defecto. Elige un fondo y dos colores de acento.
- **Textos con tu estilo.** Mantén los comandos del protocolo (`TEST`, `STOP`, `MARK HIT`) porque la app los envía tal cual, pero títulos, mensajes de estado y etiquetas los escribes tú.
- **Forma de elegir la celda.** Dos sliders es lo mínimo. Una cuadrícula tocable o un mapa es más original, pero requiere más bloques. Elige una y justifícala.
- **Nombres de componentes propios.** Usa un prefijo tuyo, no los de esta guía.
- **Formato del registro propio.** Por ejemplo: `Disparo 3: (12,7) -> impacto`, en vez de las líneas crudas.
- **Un detalle de experiencia:** vibración al recibir `OK MARK` (`Notifier1.Vibrate`, verificar en App Inventor) o un sonido.
- **No copies** el `.aia` ni las pantallas de otro grupo.

---

## 9. Exportar y guardar versiones (evidencia)

1. Dentro de App Inventor: **Projects → Save project**. Guarda en la nube de App Inventor.
2. **Projects → Export selected project (.aia) to my computer**. Se descarga un archivo `.aia`. Es un zip con el diseño y los bloques.
3. Renómbralo con la fecha y un número de versión: `duelo-app_AAAA-MM-DD_vN.aia`. Por ejemplo `duelo-app_2026-11-03_v1.aia`.
4. Guarda una versión **en cada hito**: primer PONG, primer disparo, primer TEST completo, versión final. Para cada hito, guarda también una captura del registro.
5. Para recuperar una versión: **Projects → Import project (.aia) from my computer**.
6. Para crear una copia antes de un cambio grande: **Projects → Save project as...**. Así no pierdes lo que ya funciona.

Guarda las versiones en una carpeta de evidencia que acuerde el equipo. No las mezcles con el código de `src/`.

---

## 10. Problemas frecuentes

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `DUELO-A` no aparece en Bluetooth | módulo apagado, firmware sin cargar o puente MAINT puesto | Revisa la alimentación y el puente MAINT. Reinicia y espera 10 s |
| Conectar falla | no está vinculado, ya hay otro celular conectado o faltan permisos | Vincula en Ajustes, pulsa Desconectar en el otro celular y revisa los permisos |
| No llega `PONG` | falta el salto de línea `\n` al enviar | Revisa la sección 5.2. Prueba con el comando libre `PING` |
| `ERR FORMAT` al disparar | falta un paréntesis o una coma | Revisa el texto que se envía en el registro. Debe ser `(x,y)` |
| Las líneas llegan cortadas o mezcladas | la lectura por línea no es suficiente | Usa la versión con buffer (5.9) |
| La app se congela un instante al leer | `ReceiveTextUntilDelimiter` espera una línea incompleta | Usa la versión con buffer (5.9) |
| Desconexión al bloquear la pantalla | Android suspende la app en segundo plano | Mantén la pantalla encendida durante las pruebas. Comprueba si esto ocurre (verificar en App Inventor) |
| `ERR BUSY` | enviaste una orden antes de que terminara la anterior | Espera el `OK`. DISPARAR avisa "Espera" si hay una orden en curso; el comando libre no lo hace |

---

## Referencias

- `docs/03-firmware-y-app/PROTOCOLO.md`: el contrato de líneas (la verdad).
- `docs/03-firmware-y-app/BRINGUP.md`: puesta en marcha del hardware, paso a paso.
- `docs/02-electronica/PINOUT.md`: conexiones y alimentación.
- `include/config.h`: nombres de dispositivo, tiempos y límites.
