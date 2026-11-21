# SONAR · app Android (Vite + Preact + TypeScript + Capacitor 8)

APK nativa de Batalla Naval. La UI se compila con Vite a `www/` y Capacitor la empaqueta (funciona offline).
Plan y arquitectura: `../docs/03-firmware-y-app/APP_SONAR.md`.

## Requisitos
- Node >= 18 y npm; Python >= 3.10 (build) y `uv` (solo para regenerar iconos).
- **JDK = JBR de Android Studio**: `C:\Program Files\Android\Android Studio\jbr` (el `java` del PATH es 1.8 y no sirve). Otra ruta: variable `SONAR_JAVA_HOME`.
- Android SDK en `%LOCALAPPDATA%\Android\Sdk` (platform 36, build-tools 36.x). Otra ruta: `ANDROID_HOME`.
- Primera vez: `npm install`. (`android/` ya está generado; no hace falta `cap add`.)

## Compilar
```
npm run apk                 # tsc + vite build -> cap sync -> gradlew assembleDebug -> dist-apk/
npm run apk -- --skip-typecheck   # sin tsc (si otro módulo está a medias)
npm run apk -- --no-web           # reutiliza www/ tal cual
```
Resultado: `dist-apk/SONAR-<versión>-debug.apk` (versión = `package.json`; `versionCode = major*10000 + minor*100 + patch`).
El script fija JAVA_HOME/ANDROID_HOME y al final imprime el resumen de `aapt2 dump badging`.

## Instalar en el celular
```
adb devices
adb install -r dist-apk\SONAR-0.1.0-debug.apk
```
(o `npm run apk -- --install`). Al abrir, la app pide los permisos de Bluetooth (Android 12+: Dispositivos cercanos).
El módulo ESP32 debe estar **emparejado antes** en Ajustes › Bluetooth (`SONAR-A` / `SONAR-B`).

## Piezas nativas
| Qué | Dónde |
|---|---|
| Permisos, orientación vertical, tema oscuro, etiqueta «SONAR» | `android/app/src/main/AndroidManifest.xml`, `res/values/styles.xml` |
| HTTP en claro **solo** a 192.168.4.1 (Wi-Fi mantenimiento) | `res/xml/network_security_config.xml` + `CapacitorHttp` en `capacitor.config.ts` |
| Plugin local `SonarBt` (permisos BT en runtime, lista de emparejados, encender BT, atar a Wi-Fi) | `android/.../SonarBtPlugin.java`, registrado en `MainActivity.java` |
| Versión | `android/app/build.gradle` lee `package.json` |
| Icono adaptativo + monocromo + legacy | `npm run icons` (`tools/make_icons.py`, Pillow) |
| Splash oscuro sin parpadeo | `res/values/styles.xml` + `res/drawable/splash_icon.xml` |

## Transportes (`src/transport/`)
`BluetoothTransport` (SPP), `WifiTransport` (HTTP `/cmd?l=`), `SimTransport` (otro agente). Framing/cola puros en `framing.ts`.
Pruebas: `npx vitest run src/transport`. Lo que NO se puede probar sin ESP32: ver informe de entrega.

## Calibrar apuntado (pestaña Enlace)
Sirve para que el módulo sepa **dónde está cada celda** de la matriz real, sea cual sea el montaje (pared vertical, tablero horizontal, maqueta de cartón). Necesita un firmware que anuncie `grid` en `HELLO` (protocolo v3, ver `../docs/03-firmware-y-app/PROTOCOLO.md`).

1. **Conecta** el módulo (Enlace) y baja a «Calibrar apuntado». Pulsa **90°** para centrar los servos.
2. **Enciende el láser** (se apaga solo a los 120 s; la app muestra la cuenta atrás). Si ← → o ↑ ↓ mueven al revés de lo que ves, marca «Invertir».
3. **Lleva el punto a cada esquina** de la matriz con la cruceta (pasos de 5°, 1°, 0,2° y 0,05°; mantener pulsado repite) y pulsa «Esta es la esquina…» en el orden (1,1) abajo-izquierda → (20,1) → (20,20) → (1,20). Opcional: el punto de control (11,11).
4. **CALCULAR**: el módulo ajusta el mapa con las 4 esquinas y la app muestra el error del control (debe ser pequeño, p. ej. < 0,3°).
5. **Verifica** tocando celdas del mini-tablero (el láser apunta ahí) y mira que caiga en la casilla correcta. Si no, repite la esquina que falle y recalcula.
6. **GUARDAR EN EL MÓDULO** (sobrevive al apagado). «Reiniciar mapa» borra el mapa y vuelve a la geometría de fábrica. Con la matriz final, repite 2–6 una vez más.

Código: `src/state/calib.ts` (estado y acciones; los JOG repetidos se unen en uno solo mientras hay uno en vuelo), `src/ui/views/Calibrar.tsx`, módulo simulado con gimbal virtual en `src/transport/gimbal.ts` + `sim.ts`. Prueba e2e: `uv run --script tools/e2e_calibrar.py --url http://localhost:4173/` (capturas en `../registro/2026-11-21-calibracion/`).
