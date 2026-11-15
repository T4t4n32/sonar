import type { CapacitorConfig } from '@capacitor/cli'

/**
 * Empaquetado Android (APK) para SONAR.
 * La app se compila con Vite a app/www/ (npm run build) y el APK la incluye: funciona offline.
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
    // HTTP nativo: el WebView sirve la app por https y bloquea http:// (contenido mixto);
    // con esto el transporte Wi-Fi (http://192.168.4.1) sale por HttpURLConnection.
    CapacitorHttp: { enabled: true },
  },
}

export default config