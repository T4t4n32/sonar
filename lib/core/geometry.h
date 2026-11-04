#pragma once
// Geometría de apuntado. PURO C++ (sin Arduino). Contrato compartido: no cambiar firmas sin avisar.
//
// Marco: origen = esquina posterior-izquierda de la matriz (la más cercana a la estación), x → derecha,
// y → hacia el frente (se aleja de la estación). Celdas 1..cfg::GRID_N; el centro de la celda i es (i-0.5)*cfg::CELL_MM.
// pan: 0 = hacia el frente, + = derecha. tilt: grados BAJO la horizontal.
// Ecuaciones: pan = atan2(dx, dy); tilt = atan2(h, hypot(dx, dy)); con dx = x - xs, dy = y - ys.
#include <stdint.h>

namespace core {

struct Cell { int x; int y; };
struct Station { float xMm; float yMm; float hMm; };      // eje de pan (x,y) y altura del eje de tilt sobre la matriz
struct Aim { bool ok; float panDeg; float tiltDeg; };

bool cellInRange(int x, int y);                           // 1..GRID_N en ambos ejes
Station defaultStation();                                 // cfg::STATION_X_MM, STATION_Y_MM, TILT_H_MM
Aim aimAtCell(Cell c, const Station& s);                  // ok=false si la celda está fuera de rango o excede los límites de cfg (pan, tilt)
Aim aimAtMm(float xMm, float yMm, const Station& s);      // ídem para un punto en mm (sin comprobar rango de celdas)

struct Calibration {
  Station station;                                        // x, y, h medidos en el prototipo
  float panTrimDeg;                                       // se suma al ángulo de servo de pan
  float tiltTrimDeg;                                      // se suma al ángulo de servo de tilt
};
Calibration defaultCalibration();                         // station = defaultStation(), trims = 0

struct ServoCmd { float panServoDeg; float tiltServoDeg; };   // 0..180
// pan:  cfg::PAN_CENTER_SERVO_DEG  + cfg::PAN_SIGN  * pan  + panTrim
// tilt: cfg::TILT_HORIZ_SERVO_DEG  + cfg::TILT_SIGN * tilt + tiltTrim      (recortado a 0..180)
ServoCmd toServo(const Aim& a, const Calibration& c);

// Aproximación siempre desde el mismo lado (elimina la holgura de engranes):
// si target < current → hay que pasar primero por waypoint = target - overshoot; si no, ningún waypoint.
struct Approach { bool needsWaypoint; float waypointDeg; };
Approach approach(float currentDeg, float targetDeg, float overshootDeg);

// Serialización de la calibración para NVS: 'D','L', versión (=1), 5 floats little-endian
// (xMm, yMm, hMm, panTrimDeg, tiltTrimDeg), CRC16-CCITT (poly 0x1021, init 0xFFFF) de los 23 bytes anteriores, little-endian.
constexpr unsigned CAL_BLOB_SIZE = 25;
unsigned calSerialize(const Calibration& c, unsigned char* out, unsigned cap);   // devuelve CAL_BLOB_SIZE, o 0 si cap < CAL_BLOB_SIZE
bool calDeserialize(const unsigned char* in, unsigned n, Calibration& out);      // false si n != CAL_BLOB_SIZE, magia, versión o CRC inválidos

}  // namespace core
