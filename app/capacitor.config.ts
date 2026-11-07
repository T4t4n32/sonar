import type { CapacitorConfig } from '@capacitor/cli'

/**
 * Empaquetado Android (APK) para SONAR.
 * La web va en app/www/ (copiada desde ../web/index.html por sync-web.py).
 * webDir = 'www' → el APK incluye la web y funciona offline.
 */
const config: CapacitorConfig = {
  appId: 'com.sonar.batallanaval',
  appName: 'SONAR',
  webDir: 'www',
  backgroundColor: '#040a0f',
  android: {
    allowMixedContent: false,
    backgroundColor: '#040a0f',
  },
  plugins: {
    BluetoothSerial: {
      // El plugin @e-is/capacitor-bluetooth-serial declara sus permisos en su plugin.xml.
      // Si faltrasen, se añaden manualmente en android/app/src/main/AndroidManifest.xml (ver paso 4).
    },
  },
}

export default config