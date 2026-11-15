# SONAR — arquitectura para que sirva a todos

Escrito 2026-11-07. Responde: **¿cómo hacemos que cualquier celular (Android e iPhone) se conecte rápido y que la app la pueda tener más gente, sin
rehacer nada después?** Etiquetas: ✅ verificado (fuente o prueba) · 🧭 recomendación de diseño · 🔬 solo se sabe probando en hardware.
Fuentes al final. Reglas de la rúbrica: Bluetooth desde el celular con app propia; test de 5 posiciones; software original.

## 1. Decisión central (una frase)
> **Un solo protocolo, varios transportes intercambiables, una sola interfaz con dos presentaciones (ligera en el ESP32, rica en el APK).**
> El camino «para todos» es **Wi-Fi + QR + página servida por el propio ESP32**; el camino «de la rúbrica» es el **APK Android por Bluetooth**.
> Los dos **no se encienden a la vez** (modos que se cambian por comando).

## 2. Qué llega a cada celular (alcance real)
| Vía | Android | iPhone | PC | Veredicto |
|---|---|---|---|---|
| Página servida por el ESP32 (Wi-Fi) | ✅ | ✅ | ✅ | **Línea base universal** (cero instalación) |
| APK con Bluetooth clásico (SPP) | ✅ (plugin nativo) | ❌ (SPP exige MFi) 🧭 | — | **Camino de la rúbrica** |
| Web Bluetooth (BLE) | ✅ Chrome/Edge, solo https | ❌ Safari; solo con navegadores tipo Bluefy | ✅ Chrome/Edge | **Reabierto 2026-11-07** (idea de Sebas: página tipo Dado que pide el Bluetooth): exige un transporte **BLE** en el firmware (entorno aparte, sin tocar `modulo_a`) y no sirve en iPhone; solo si Almario acepta «web = app». Hay que alojarla en https sin publicar el enlace antes del 24-nov |
| PWA en https hablando con el ESP32 | pide permiso de red local desde Chrome 142 | sin verificar | idem | Solo para **demo simulada y documentación**, no para controlar |
| `sonar.local` (mDNS) | solo Android 12+, resultados mixtos | sin verificar | sin verificar | No se usa: la IP `192.168.4.1` es la única garantía |

Consecuencia: **iPhone solo entra por Wi-Fi**. Por eso el Wi-Fi no es «un extra»: es lo que cumple «para todos».

## 3. Capas (para no batallar después)
```
 Celular / PC
 ┌──────────────────────────── SONAR UI (un código) ────────────────────────────┐
 │ presentación LIGERA (≤60 KB, gz) │ presentación RICA (animaciones, zona de pelea) │
 │            ESP32 la sirve         │              dentro del APK / PWA              │
 ├───────────────────────────── cliente de protocolo ────────────────────────────┤
 │  Transporte:  WS (Wi-Fi) · SPP nativo (APK) · HTTP (compat.) · Simulado (demo) │
 └───────────────────────────────────────────────────────────────────────────────┘
                              │ líneas de texto (PROTOCOLO.md, no se rompe)
 ESP32 ┌───────────────────────┴───────────────────────────────────────────────────┐
       │ LineTransport: USB · BT-SPP · WS · (opcional ESP-NOW)   ← piezas intercambiables│
       │ core: protocolo · geometría · controlador (no sabe por cuál canal le llega) │
       └────────────────────────────────────────────────────────────────────────────┘
```
- ✅ El firmware **ya** tiene esta forma (`LineTransport`, `g_links[]`, `idleHook` que atiende `STOP`/`ERR BUSY` en todos los canales durante un disparo).
- 🧭 Añadir `WsTransport`: una cola segura entre la tarea del servidor asíncrono y `readLine()`, que el `idleHook` ya consulta. **El núcleo no cambia.**
  Efecto: `STOP` por Wi-Fi corta de verdad, el `TEST` puede informar cada posición en vivo y varios celulares ven los mismos eventos.

## 4. Modos (no Bluetooth y Wi-Fi a la vez)
| Modo | Qué enciende | Para qué |
|---|---|---|
| **BT** (hoy por defecto) | USB + Bluetooth SPP | rúbrica, control 1, test; un solo celular |
| **WIFI** | USB + SoftAP + portal cautivo + servidor asíncrono/WS | cualquier celular, varios clientes, duelo, calibración |
- ✅ La tabla de coexistencia de Espressif marca **BR/EDR + SoftAP conectado como «soportado, rendimiento inestable»**, y hay reportes de ~45 KB menos de heap al activar Wi-Fi.
  Por eso **no** se enciende todo junto por defecto. 🔬 Si algún día se quiere, medir antes.
- 🧭 Cambio de modo **sin tocar hardware**: orden `MODE WIFI` / `MODE BT` → guarda en NVS y reinicia (~2 s). Recuperación: mantener `BTN_TEST` al arrancar = modo BT.
  (Hoy el modo lo decide el pin `MAINT`; se conserva como forzado.)

## 5. Conexión rápida (meta: ≤ 20 s hasta el primer disparo 🔬)
- **Wi-Fi:** QR pegado al módulo (`WIFI:T:WPA;S:SONAR-A;P:clave;;`) → tocar el aviso → el portal abre la página.
  ✅ Android y iOS piden **un toque/confirmación**; no se une solo. ✅ El portal cautivo exige DNS que resuelva todo a `192.168.4.1` y **redirigir (302)** las sondas
  (`/generate_204`, `/hotspot-detect.html`, `/connecttest.txt`, `/redirect`); responder 200/204 hace que el celular crea que hay internet y no abra nada.
  🔬 Verificar en Android 13-15 e iOS 17-26 (los textos hallados son de 2017-2023). Respaldo: escribir `192.168.4.1` a mano.
  Aviso «sin internet»: ✅ existe; 🔬 sin solución confirmada para versiones actuales. El mini-navegador del portal puede ser limitado: botón «Abrir en Chrome/Safari».
- **Bluetooth (APK):** emparejar una vez; la app lista los módulos emparejados y reconecta sola. 🔬 `SerialBT.enableSSP()` (emparejamiento sin PIN) y reconexión según el celular.
- **Medición honesta:** cronómetro con A04s, 13C y un iPhone prestado; se registra en `registro/` (no se promete 20 s sin medirlo).

## 6. Seguridad del láser con control remoto 🧭 (requisito, no adorno)
El Wi-Fi puede estar al alcance de extraños y el KY-008 es un láser (clase por confirmar con la etiqueta). Reglas:
1. **Armado físico:** el láser no responde a disparos remotos hasta que se pulsa el botón del módulo (LED parpadea) y se desarma solo a los 60 s. `STOP` **siempre** se acepta.
2. Red Wi-Fi **WPA2** con clave en el QR (no abierta).
3. «Hombre muerto»: si se pierde el latido del WebSocket durante un disparo, se apaga el láser.
4. Un solo cliente puede disparar a la vez (los demás solo observan).
(La búsqueda no halló una norma específica: son patrones estándar, **no verificados** contra una norma.)

## 7. Protocolo v2 (compatible hacia atrás)
Se conserva todo `PROTOCOLO.md`. Se añade, sin romper nada: `HELLO` → `HELLO SONAR 2 <fw> <nombre> <modo> <caps>` (las páginas se adaptan);
`MODE …`; `ARM`; líneas de evento no solicitadas con prefijo `EVT ` (p. ej. `EVT TEST 3 OK (20,20)`, `EVT BUSY`), para el envío en vivo por WS.
Se prueban en `lib/core` con Unity como el resto.

## 8. Duelo entre dos jugadores (diseño abierto, depende de Almario)
- **T1 (recomendado):** el atacante se conecta al módulo que recibe el disparo (como ya aclaraste). Con **Wi-Fi** caben varios clientes: atacante y dueño ven los mismos
  eventos en vivo y el dueño marca `TOCADO/AGUA`. Con Bluetooth SPP hay **un solo cliente**: el marcado lo hace el mismo celular.
- **T2:** enlace módulo↔módulo con ESP-NOW. ✅ Espressif lo da como **no estable en recepción cuando el módulo es SoftAP** y ata el canal al del Wi-Fi: solo si T1 estorba, y con medición 🔬.
- Pendiente de Almario: quién dispara sobre qué tablero; contra quién es la prueba; si una web cuenta como app.

## 9. Distribución pública (después de la entrega)
- 🧭 **Repositorio privado hasta el 24-nov**; publicar con fecha posterior y licencia clara (la rúbrica penaliza copias: pregúntale a Almario si publicar cuenta).
- Código **MIT o Apache-2.0**; documentación **CC BY-SA 4.0**; hardware **CERN-OHL**. Antes: revisar **todo el historial** de git por claves Wi-Fi, `.jks`, datos personales; `secrets.h` ignorado + `.example`.
- ✅ **APK en GitHub Releases + QR.** Verificación de desarrolladores de Google: arranca el 30-sep-2026 en Brasil, Indonesia, Singapur y Tailandia; expansión global en 2027 (**Colombia no está en la primera fase**);
  existe cuenta gratuita de «distribución limitada» (hasta 20 dispositivos) para estudiantes. Se registra más adelante si hace falta.
- ✅ **Google Play: no compensa** (12 probadores × 14 días para cuentas personales nuevas).
- ✅ **Flasheo para otros:** ESP Web Tools (manifest + `.bin`, https, **PC con Chrome/Edge**); Chrome Android 🔬 sin verificar.
- PWA en GitHub Pages: página de inicio, **demo simulada** y documentación (en iPhone no se conserva el almacenamiento si no se instala: ✅ fuentes secundarias).

## 10. Fases (hoy es 2026-11-07)
| Fase | Fecha | Entregable | Prueba que la cierra |
|---|---|---|---|
| **F0 Control 1** | hasta dom 8-nov | Bluetooth real: celular manda `(x,y)` y el láser cae 5/5 | `PING` por «Serial Bluetooth Terminal»; `BRINGUP.md` |
| **F1 Cimientos** | 8 → 15-nov | Modos + portal cautivo + `WsTransport` + `HELLO/MODE/ARM`; UI en transportes; build ligera gz | spikes §11; heap medido; `STOP` en vivo por Wi-Fi |
| **F2 Todo** | 15 → 20-nov | APK rico (SPP, asistente de calibración, zona de pelea T1, modo laboratorio) | control 2/3, prueba con contrincante, video |
| **F3 Congelar** | 20 → 22-nov | firmware y app congelados, repo limpio, registro | `e2e_web.py`, `pio test`, cronómetro de conexión |
| **F4 Publicar** | después del 24-nov | GitHub público, Pages, Releases, ESP Web Tools | historial revisado, licencias |

Donde se ganan décimas: **test 2,0** (asistente de calibración que corrige el desvío de cada una de las 5 posiciones), **estética 0,5**, **sustentación 1,0** (modo laboratorio + bitácora), **video 0,5** (modo demostración).

## 11. Spikes (convierten «no verificado» en hecho)
| # | Qué | Cómo | Estado |
|---|---|---|---|
| S1 | ¿Compila ESPAsyncWebServer + WebSocket + DNS + BluetoothSerial en Arduino-ESP32 2.0.17? | compilar un esqueleto | ✅ **Sí** (2026-11-07): ESPAsyncWebServer 3.12.1 + AsyncTCP 3.5.0 compilan con BluetoothSerial, DNSServer y WebSocket; RAM estática 18,0 % (59 144 B), flash 50,1 % (1 575 189 B de 3 MB). **Solo compila**: el heap libre en ejecución sigue en S2 |
| S2 | Heap libre y mayor bloque contiguo con Wi-Fi + WS (modo WIFI) y con BT (modo BT) | `heap_caps_get_largest_free_block` en el ESP32 | 🔬 hardware |
| S3 | ¿Abren el portal solos el A04s, el 13C y un iPhone? Tiempo hasta el primer disparo | cronómetro, 3 celulares | 🔬 hardware |
| S4 | Emparejamiento sin PIN (`enableSSP`) y reconexión en A04s/13C | prueba manual | 🔬 hardware |
| S5 | Latencia de `STOP` por WS con 1-3 clientes | medir con `sim_phone` + celulares | 🔬 hardware |
| S6 | ESP-NOW RX con SoftAP (solo si se necesita T2) | dos módulos | 🔬 hardware, opcional |

## Fuentes (consultadas 2026-11-07; casi ninguna es de 2026)
Coexistencia ESP32: docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/coexist.html · heap con Wi-Fi: github.com/espressif/arduino-esp32/issues/8033 ·
servidor asíncrono: github.com/ESP32Async/ESPAsyncWebServer · portal cautivo: isc.sans.edu/diary/33172 · Web Bluetooth: github.com/WebBluetoothCG/web-bluetooth (implementation-status) ·
red local en Chrome: developer.chrome.com/blog/local-network-access · verificación de desarrolladores: developer.android.com/developer-verification ·
Play (testers): support.google.com/googleplay/android-developer/answer/14151465 · ESP Web Tools: github.com/esphome/esp-web-tools.
Lo marcado 🔬 no tiene fuente: se decide midiendo.
