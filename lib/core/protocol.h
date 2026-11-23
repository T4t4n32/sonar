#pragma once
// Protocolo de líneas de texto (ver docs/03-firmware-y-app/PROTOCOLO.md). PURO C++ (sin Arduino). Contrato compartido.
#include <string>

namespace core {

enum class CmdType { Fire, Test, Stop, Ping, CalShow, CalSet, CalSave, CalReset, MarkHit, MarkMiss, Hello, Mode, Arm,
                     // Protocolo v3 (calibración por esquinas)
                     Pt, Jog, Goto, LaserOn, LaserOff, LaserQuery, Corner, Corners, CalFit, CalMap, Aim,
                     Pts,     // Pts: estado de los 9 puntos de calibración
                     Info };  // Info: diagnóstico (arranque, memoria, posición de los servos, mapa activo)
enum class ParseError { None, Empty, TooLong, BadFormat, Range, Unknown };

struct Command {
  CmdType type = CmdType::Ping;
  int x = 0, y = 0;                 // Fire
  float cal[5] = {0, 0, 0, 0, 0};   // CalSet: xs ys h panTrim tiltTrim
  int mode = 0;                     // Mode: 0 = consulta, 1 = BT, 2 = WIFI
  float a = 0, b = 0;               // Jog: dpan dtilt (grados de servo); Goto: pan tilt absolutos
                                    // Corner: x = n (1..9); Aim: x, y (celda 1..GRID_N)
};
struct ParseResult { ParseError err = ParseError::None; Command cmd; };

constexpr unsigned MAX_LINE = 64;

// Tolerante con espacios, \r\n y mayúsculas/minúsculas. "(x,y)" EXIGE paréntesis; x,y enteros en 1..cfg::GRID_N.
//   "(12,7)" / "( 12 , 7 )" → Fire;  "TEST","STOP","PING","CAL SHOW","CAL SET a b c d e","CAL SAVE","CAL RESET","MARK HIT","MARK MISS".
// Protocolo v2: "HELLO", "ARM" (consulta), "MODE" (consulta) y "MODE BT" / "MODE WIFI". "MODE X" desconocido → Unknown.
// Protocolo v3: "PT", "JOG a b" (|a|,|b| <= JOG_MAX_DEG), "GOTO p t" (SERVO_SAFE_MIN..MAX), "LASER" / "LASER ON" / "LASER OFF",
// "CORNER n" (1..9; 6..9 = medios de borde opcionales), "CORNERS" (los 5 primeros), "PTS" (los 9), "INFO" (diagnóstico), "CAL FIT", "CAL MAP", "AIM x y" (enteros 1..GRID_N, sin paréntesis).
// Errores: línea vacía → Empty; > MAX_LINE → TooLong; "(a,b)" no numérico o sintaxis mala → BadFormat;
// enteros fuera de 1..GRID_N → Range; palabra desconocida → Unknown. CAL SET exige 5 números → si no, BadFormat.
ParseResult parseLine(const std::string& line);

std::string errorText(ParseError e);          // "ERR EMPTY" | "ERR TOOLONG" | "ERR FORMAT" | "ERR RANGE" | "ERR UNKNOWN" ("" si None)
std::string fireOkText(int x, int y);         // "OK (x,y)"

}  // namespace core
