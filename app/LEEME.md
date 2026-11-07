# SONAR — Android Wrapper (Capacitor)

Empaqueta la interfaz web `../web/index.html` como APK Android usando **Capacitor v8**.
Esta versión **solo envuelve la web**; el transporte Bluetooth real se añade después.

---

## Requisitos previos

| Herramienta | Versión / Ruta | Notas |
|-------------|----------------|-------|
| **Node.js** | ≥ 18 (LTS) | `node -v` |
| **npm** | ≥ 9 | `npm -v` |
| **Python** | ≥ 3.8 | `python --version` |
| **JDK** | JBR de Android Studio | `JAVA_HOME=C:\Program Files\Android\Android Studio\jbr` |
| **Android SDK** | `<usuario>\AppData\Local\Android\Sdk` | `ANDROID_HOME` apuntando aquí |
| **Build Tools** | 36.x (en SDK) | `aapt2` para verificación final |

> **Importante:** El `java` del PATH del sistema es 1.8 y **no sirve**. Usa el JBR de Android Studio:
> ```cmd
> set JAVA_HOME=C:\Program Files\Android\Android Studio\jbr
> set PATH=%JAVA_HOME%\bin;%PATH%
> ```

---

## Estructura del proyecto

```
app/
├── package.json           # Dependencias Capacitor v8 + plugin Bluetooth
├── capacitor.config.ts    # appId: com.sonar.batallanaval, webDir: www
├── sync-web.py            # Copia ../web/index.html → www/index.html
├── www/                   # Generado por sync-web.py (no versionar)
├── android/               # Generado por `npx cap add android`
└── dist-apk/              # APK final (creado al compilar)
```

---

## Comandos para reconstruir (orden exacto)

```cmd
cd I:\repository\Batalla Naval - Sonar\sonar\app

# 1. Instalar dependencias (una sola vez)
npm install

# 2. Añadir plataforma Android (una sola vez)
npx cap add android

# 3. Sincronizar la web actual al proyecto Android
python sync-web.py
npx cap sync android

# 4. Compilar APK debug
cd android
gradlew.bat assembleDebug
```

El APK resultante estará en:
```
app/android/app/build/outputs/apk/debug/app-debug.apk
```
Se copia a `app/dist-apk/SONAR-0.0.1-debug.apk` como entrega final.

---

## Verificación del APK

```cmd
# Ver package name y permisos
"%ANDROID_HOME%\build-tools\36.0.0\aapt2.exe" dump badging app/dist-apk/SONAR-0.0.1-debug.apk
```

Salida esperada (fragmento):
```
package: name='com.sonar.batallanaval' versionCode='1' versionName='0.0.1'
...
uses-permission: name='android.permission.BLUETOOTH'
uses-permission: name='android.permission.BLUETOOTH_ADMIN'
uses-permission: name='android.permission.BLUETOOTH_CONNECT'
uses-permission: name='android.permission.BLUETOOTH_SCAN'
uses-permission: name='android.permission.ACCESS_FINE_LOCATION'
uses-permission: name='android.permission.INTERNET'
```

---

## Qué falta (próximos pasos)

1. **Transporte Bluetooth real**: La web usa `fetch('/cmd?l=...')` hacia Wi-Fi (ESP32). Hay que:
   - Exponer una API Capacitor (`BluetoothSerial` del plugin `@e-is/capacitor-bluetooth-serial`).
   - Inyectar un *bridge* en `www/index.html` que redirija `send()`/`cmd()` al plugin nativo.
   - Manejar permisos de runtime (`BLUETOOTH_CONNECT`, `BLUETOOTH_SCAN`) en `MainActivity`.

2. **Iconos y splash**: Generar `mipmap/ic_launcher` y `drawable/splash` con `npx cap sync` tras añadir recursos en `android/app/src/main/res/`.

3. **Firma de release**: Configurar `keystore.properties` (fuera de git) y `signingConfigs.release` en `android/app/build.gradle` cuando se vaya a Play Store.

4. **Pruebas en dispositivo real**: El emulador no tiene Bluetooth clásico; probar en físico.

---

## Notas sobre el plugin Bluetooth

- Plugin: `@e-is/capacitor-bluetooth-serial@6.0.3` (última compatible con Capacitor 6; se usa en Capacitor 8 *as-is*).
- Declara en su `AndroidManifest`:
  - `BLUETOOTH`, `BLUETOOTH_ADMIN` (maxSdkVersion 30)
  - `BLUETOOTH_CONNECT`, `BLUETOOTH_SCAN` (tools:targetApi="s")
  - `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`
- **Este wrapper añade** en `app/src/main/AndroidManifest.xml`:
  - `BLUETOOTH_SCAN` con `usesPermissionFlags="neverForLocation"` (evita pedir ubicación en Android 12+).
  - `ACCESS_FINE_LOCATION` con `maxSdkVersion="30"` (solo legacy).

---

## Limpieza

```cmd
cd app\android
gradlew.bat clean
gradlew.bat --stop
```