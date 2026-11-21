#pragma once
// Mapa de apuntado por esquinas (calibración medida en la maqueta real). PURO C++ (sin Arduino).
//
// El operador apunta el láser a las 4 esquinas de la matriz y el módulo guarda los ángulos de servo de cada una.
// Con ellas se ajusta una HOMOGRAFÍA entre las coordenadas de la matriz y la dirección del rayo, de modo que
// cualquier celda (x,y) se traduce a (pan, tilt) sin saber la geometría (plano vertical u horizontal, distancia, altura).
//
// Dirección del rayo en un cardán ideal (pan sobre eje vertical, tilt sobre eje horizontal), con θ = pan y φ = tilt
// medidos desde el centro del servo: u = tan θ, v = tan φ / cos θ. La proyección del plano de la matriz sobre (u, v)
// es exactamente una homografía; la inversa es θ = atan u, φ = atan(v cos θ).
#include <stdint.h>

namespace core {

constexpr int GRID_PTS = 5;   // 4 esquinas + 1 punto de control

struct GridCal {
  bool has[GRID_PTS] = {false, false, false, false, false};
  float pan[GRID_PTS] = {0, 0, 0, 0, 0};    // ángulos de servo (0..180) registrados en cada punto
  float tilt[GRID_PTS] = {0, 0, 0, 0, 0};
  bool valid = false;                       // la homografía está calculada y es utilizable
  double h[8] = {0, 0, 0, 0, 0, 0, 0, 0};   // h11 h12 h13 h21 h22 h23 h31 h32 (h33 = 1), sobre coordenadas normalizadas
};

// Celda a la que corresponde cada punto: 0=(1,1) 1=(20,1) 2=(20,20) 3=(1,20) 4=(11,11) (control).
void gridPointCell(int n, int& x, int& y);
bool gridHasCorners(const GridCal& g);   // las 4 esquinas registradas

// Ajusta la homografía con las 4 esquinas. false si faltan esquinas o la configuración es degenerada (colineales, etc.).
// `checkErrDeg` = error máximo (grados de servo) al predecir el punto de control; -1 si no hay punto de control.
bool gridFit(GridCal& g, float& checkErrDeg);

// Ángulos de servo para la celda (x,y) con el mapa ajustado. false si !valid, celda fuera de 1..20 o resultado no finito.
bool gridAim(const GridCal& g, int x, int y, float& panServo, float& tiltServo);

// Serialización para NVS: 'G','M', versión (=1), banderas (bits 0..4 = has, bit 5 = valid), 10 floats little-endian
// (pan[5], tilt[5]), CRC16-CCITT de los 44 bytes anteriores, little-endian. La homografía se recalcula al leer.
constexpr unsigned GRID_BLOB_SIZE = 46;
unsigned gridSerialize(const GridCal& g, unsigned char* out, unsigned cap);   // GRID_BLOB_SIZE, o 0 si cap es corto
bool gridDeserialize(const unsigned char* in, unsigned n, GridCal& out);      // false si tamaño, magia, versión o CRC fallan

}  // namespace core
