# Plan de Conexiones Electrónicas y Distribución de Hardware — SONAR

Este documento detalla el esquema de conexiones físicas, el sistema de alimentación eléctrica, el aislamiento de ruido y la arquitectura de la matriz de fotorresistencias (LDR) para el proyecto **SONAR** (ESP32 / Pan-Tilt / Láser).

---

## 1. Mapa General de Pines (ESP32 WROOM-32)

| Componente / Función | GPIO ESP32 | Descripción Eléctrica y Conexión |
|---|---|---|
| Servo **Pan** (Base) | **GPIO 18** | PWM a 50 Hz (LEDC canal 0). Señal de control. |
| Servo **Tilt** (Elevación) | **GPIO 19** | PWM a 50 Hz (LEDC canal 1). Señal de control. |
| Diodo **Láser** (KY-008) | **GPIO 23** | Salida digital → Resistencia $1\text{ k}\Omega$ → Base transistor 2N2222A (Pull-down $10\text{ k}\Omega$ a GND para evitar disparos en boot). |
| Zumbador Activo | **GPIO 21** | Salida tono de acierto/fallo. |
| LED de Estado / Acierto | **GPIO 22** | Salida digital → Resistencia $330\Omega$ → LED indicador. |
| Pulsador TEST | **GPIO 25** | Entrada digital con pull-up interno (`INPUT_PULLUP`). Cierra a GND. |
| Interruptor MANT | **GPIO 26** | Selector de modo al arranque (GND = Modo Mantenimiento Wi-Fi, Abierto = Modo Juego Bluetooth SPP). |
| ADC Sensor / Riel | **GPIO 34** | Entrada analógica (ADC1) para lectura multiplexada de matriz LDR o monitoreo de voltaje. |

---

## 2. Diagrama de Distribución de Potencia y Aislamiento de Ruido

El mayor riesgo en sistemas mecatrónicos con ESP32 y servomotores es el **ruido inductivo** generado por los motores, que causa reinicios inesperados (Brownout / Watchdog Reset).

```
[ Fuente Externa 6V / 4A ] ---> (Conversor Buck 5V 3A) ---> [ Pin VIN / 5V ESP32 ]
            |
            +---> [ Riel 6V ] ---> Motores Servos (Pan & Tilt) + Condensador 1000 µF
            |
            +---> [ Riel 5V ] ---> Láser KY-008 + Zumbador + Electrónica MUX LDR
            |
            +---> [ GND Común ] <--- ¡OBLIGATORIO UNIR TODAS LAS MASAS!
```

### Reglas de Oro de Cableado:
1. **GND Común**: La tierra de la fuente de 6V/5V, la tierra de los servos y la tierra del ESP32 **deben** estar unidas sólidamente en un punto estrella.
2. **Condensadores de Acoplamiento**: Colocar un condensador electrolítico de $1000\,\mu\text{F}$ en paralelo con la alimentación de los servos y uno de $470\,\mu\text{F}$ en la entrada de 5V del ESP32.
3. **Alimentación Independiente**: **Nunca** alimentes los servomotores directamente desde el pin `5V` o `3.3V` de salida del regulador interno del ESP32; usa siempre la fuente externa de potencia.

---

## 3. Arquitectura del Tablero Óptico con Matriz LDR ($20 \times 20 = 400$ Celdas)

Para sensar la posición de la flota (por oclusión de luz) y confirmar el impacto del láser sin agotar los pines del ESP32, se implementa una matriz multiplexada con chips analógicos **CD74HC4067** (Multiplexores de 16 canales).

### Especificaciones del Multiplexado:
- Se requieren **25 chips CD74HC4067** para cubrir los 400 puntos de sensado.
- **Bus de Control Compartido**: Los pines de selección binaria `S0, S1, S2, S3` de todos los multiplexores se conectan en paralelo a 4 GPIOs digitales de salida del ESP32 (p.ej. GPIO 13, 14, 27, 32).
- **Habilitación (EN)**: Cada chip CD74HC4067 tiene un pin `E` (Active LOW). Mediante lógica de decodificación adicional (o registros de desplazamiento 74HC595), se habilita un solo chip a la vez durante el barrido.
- **Salida Analógica (SIG)**: La salida común del multiplexor activo se enruta a una entrada analógica del ESP32 (`GPIO 34` en ADC1).

### Circuito de Celdas LDR:
- Cada celda contiene una fotorresistencia (LDR) en serie con una resistencia fija de $10\text{ k}\Omega$ formando un divisor de tensión alimentado a $3.3\text{ V}$.
- Cuando el barco cubre la celda (oscuridad), la resistencia de la LDR sube y el voltaje analógico cae.
- Cuando el láser de $650\text{ nm}$ incide sobre la LDR, su resistencia cae abruptamente y el voltaje analógico sube ($\Delta V$). El software detecta el evento evaluando el diferencial temporal $\Delta V = V_{laser} - V_{ambient}$.
