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

constexpr int GRID_PTS = 9;   // 4 esquinas + 1 punto de control + 4 medios de borde (opcionales: afinan el ajuste)

struct GridCal {
  bool has[GRID_PTS] = {false, false, false, false, false, false, false, false, false};
  float pan[GRID_PTS] = {0, 0, 0, 0, 0, 0, 0, 0, 0};    // ángulos de servo (0..180) registrados en cada punto
  float tilt[GRID_PTS] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
  bool valid = false;                       // la homografía está calculada y es utilizable
  double h[8] = {0, 0, 0, 0, 0, 0, 0, 0};   // h11 h12 h13 h21 h22 h23 h31 h32 (h33 = 1), sobre coordenadas normalizadas
};

// Celda de cada punto: 0=(1,1) 1=(20,1) 2=(20,20) 3=(1,20) 4=(11,11) (control: nunca entra al ajuste),
// 5=(11,1) 6=(20,11) 7=(11,20) 8=(1,11) (medios de borde: si hay alguno, el ajuste es por MÍNIMOS CUADRADOS con todos los
// puntos registrados entre 0-3 y 5-8, y reparte el error de apuntado entre ellos en vez de fiarse solo de 4 puntos).
void gridPointCell(int n, int& x, int& y);
bool gridHasCorners(const GridCal& g);   // las 4 esquinas registradas

// Ajusta la homografía con las 4 esquinas (exacto) o, si hay medios de borde, con todos por mínimos cuadrados.
// false si faltan esquinas, la configuración es degenerada o algún punto queda a más de 2,5° del ajuste (apuntado equivocado).
// `checkErrDeg` = el mayor error (grados de servo): el del punto de control si lo hay y, con mínimos cuadrados, también el
// residuo de los puntos usados; -1 si no hay con qué medirlo.
bool gridFit(GridCal& g, float& checkErrDeg);

// Ángulos de servo para la celda (x,y) con el mapa ajustado. false si !valid, celda fuera de 1..20 o resultado no finito.
bool gridAim(const GridCal& g, int x, int y, float& panServo, float& tiltServo);

// Serialización para NVS, versión 2: 'G','M', 2, has[0..7] (bits), banderas (bit0 = has[8], bit1 = valid), 0 reservado,
// 18 floats little-endian (pan[9], tilt[9]), CRC16-CCITT de los 78 bytes anteriores, little-endian. La homografía se
// recalcula al leer. Se sigue leyendo la versión 1 (5 puntos, 46 bytes) para no perder una calibración ya guardada.
constexpr unsigned GRID_BLOB_SIZE = 80;
constexpr unsigned GRID_BLOB_SIZE_V1 = 46;
unsigned gridSerialize(const GridCal& g, unsigned char* out, unsigned cap);   // GRID_BLOB_SIZE, o 0 si cap es corto
bool gridDeserialize(const unsigned char* in, unsigned n, GridCal& out);      // false si tamaño, magia, versión o CRC fallan

}  // namespace core
