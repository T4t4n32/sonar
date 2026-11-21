#pragma once
// Constantes del proyecto. Unidades: mm y grados. Sin dependencias de Arduino (se usa también en las pruebas nativas).
#include <stdint.h>

#ifndef DEVICE_NAME
#define DEVICE_NAME "SONAR-A"
#endif
#ifndef WIFI_SSID_MAINT
#define WIFI_SSID_MAINT "DUELO-A-MANT"
#endif
#define WIFI_PASS_MAINT "duelo1234"
#define FW_VERSION "0.1.0"

namespace cfg {

// ---- Tablero y geometría (ver Planos y medidas: marco con origen en la esquina posterior-izquierda de la matriz)
constexpr int   GRID_N       = 20;       // celdas por lado; coordenadas (x,y) = 1..GRID_N
constexpr float CELL_MM      = 10.0f;
constexpr float STATION_X_MM = 100.0f;   // eje de pan
constexpr float STATION_Y_MM = -65.0f;
constexpr float TILT_H_MM    = 180.0f;   // altura del eje de tilt sobre la matriz

// ---- Límites de seguridad (el rayo nunca debe salir del tablero)
constexpr float PAN_LIMIT_DEG = 57.0f;   // |pan| máximo
constexpr float TILT_MIN_DEG  = 30.0f;   // bajo la horizontal
constexpr float TILT_MAX_DEG  = 72.0f;

// ---- Servos
constexpr int   SERVO_MIN_US = 500;      // 0°   (verificar con el servo real)
constexpr int   SERVO_MAX_US = 2500;     // 180°
constexpr float PAN_CENTER_SERVO_DEG  = 90.0f;   // ángulo de servo con el rayo hacia el frente
constexpr float TILT_HORIZ_SERVO_DEG  = 90.0f;   // ángulo de servo con el rayo horizontal
constexpr float PAN_SIGN  = 1.0f;        // +1: aumentar el ángulo de servo gira a la derecha
constexpr float TILT_SIGN = 1.0f;        // +1: aumentar el ángulo de servo baja el rayo
constexpr float MAX_STEP_DEG = 2.0f;     // rampa: máximo avance por paso
constexpr uint32_t STEP_MS   = 20;
constexpr float OVERSHOOT_DEG = 2.0f;    // aproximarse siempre desde el mismo lado

// ---- Calibración por esquinas (JOG / GOTO / LASER ON)
constexpr float JOG_MAX_DEG      = 20.0f;      // paso relativo máximo por orden JOG
constexpr float SERVO_SAFE_MIN   = 15.0f;      // el firmware nunca ordena ángulos fuera de este rango por JOG/GOTO/AIM
constexpr float SERVO_SAFE_MAX   = 165.0f;
constexpr uint32_t AIM_LASER_MAX_MS = 120000;  // LASER ON se apaga solo a los 120 s

// ---- Tiempos
constexpr uint32_t SETTLE_MS   = 300;    // espera tras detener los servos, antes de encender el láser
constexpr uint32_t LASER_ON_MS = 1500;
constexpr uint32_t TEST_GAP_MS = 1500;
constexpr uint32_t LED_HIT_MS  = 2000;
constexpr uint16_t BEEP_HZ = 1000;
constexpr uint16_t BEEP_MS = 150;

// ---- Rutina de TEST (5 posiciones: esquinas y centro)
constexpr int TEST_CELLS[5][2] = {{1, 1}, {20, 1}, {20, 20}, {1, 20}, {11, 11}};

// ---- Pines (ESP32 clásico; evitan strapping 0/2/12/15, flash 6-11 y pines solo-entrada para salidas)
namespace pins {
constexpr int PAN      = 18;
constexpr int TILT     = 19;
constexpr int LASER    = 23;   // a la base del 2N2222A por 1 kΩ, con 10 kΩ a GND (apagado al arrancar)
constexpr int BUZZER   = 21;   // zumbador activo
constexpr int LED      = 22;   // LED de acierto
constexpr int BTN_TEST = 25;   // pulsador a GND, pull-up interno: lanza el TEST
constexpr int MAINT    = 26;   // a GND al arrancar = modo mantenimiento (Wi-Fi); abierto = Bluetooth
constexpr int VSENSE   = 34;   // opcional: divisor del riel de 5 V (ADC1)
}  // namespace pins

}  // namespace cfg
