# Propuesta Técnica: Tablero Óptico Activo con Fotorresistencias (LDR) / Detección Láser
> Añadido al proyecto **SONAR** (Batalla Naval con ESP32) para soportar sensado automático de posición de barcos y confirmación de impacto láser.

## 1. Concepto y Desafío Físico
Sebas propone un tablero de $20 \times 20$ celdas ($400$ posiciones) donde:
1. **Detección de flota en base**: Fotorresistencias (LDRs) o fototransistores bajo cada celda. Al colocar el barco (que tapa la luz de fondo o LED inferior), se detecta dónde está ubicado sin registro manual.
2. **Impacto de láser**: Cuando la torreta Pan-Tilt dispara y el rayo láser de $650\text{ nm}$ cae sobre la celda objetivo, la LDR de esa celda experimenta un cambio brusco de resistencia (`ΔLux`), confirmando el "Tocado" de manera automática.

## 2. Viabilidad y Arquitectura del Multiplexado
Con $400$ celdas, conectar $400$ sensores analógicos directamente al ESP32 es imposible por falta de pines (el ESP32 tiene 15 canales ADC en ADC1 y ninguno utilizable con Wi-Fi en ADC2).
- **Solución Hardware**: Sistema multiplexado matricial usando **25 chips CD74HC4067** (MUX analógicos/digitales de 16 canales: $25 \times 16 = 400$).
- **Lectura Diferencial**:
  - $t_0$: Lectura ambiente con láser apagado.
  - $t_1$: Lectura con láser encendido durante $t_{pulse} = 50\text{ ms}$.
  - Condición de impacto: $\Delta V = V(t_1) - V(t_0) > \text{Threshold}$.

## 3. Integración con el Repo `sonar` (`I:\repository\Batalla Naval - Sonar\sonar`)
Se creará un nuevo módulo / target en PlatformIO (`platformio.ini`), por ejemplo `[env:modulo_optico]`, que extienda `lib/hal_esp32` con:
- `lib/hal_esp32/mux_matrix.cpp`: Rutina de barrido secuencial de los 400 canales vía MUX.
- `lib/core/sensor_grid.h`: Lógica de validación de flota y confirmación de impacto.
- `tools/sim_sensor_grid.py`: Simulador en Python para probar la matriz sin hardware físico conectado.

---
*Documento registrado por Lucky para Sebastián Sánchez Chacón y Jader Andrés Astaiza Ocampo.*
