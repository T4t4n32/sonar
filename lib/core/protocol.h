#pragma once
// Protocolo de líneas de texto (ver docs/PROTOCOLO.md). PURO C++ (sin Arduino). Contrato compartido.
#include <string>

namespace core {

enum class CmdType { Fire, Test, Stop, Ping, CalShow, CalSet, CalSave, CalReset, MarkHit, MarkMiss };
enum class ParseError { None, Empty, TooLong, BadFormat, Range, Unknown };

struct Command {
  CmdType type = CmdType::Ping;
  int x = 0, y = 0;                 // Fire
  float cal[5] = {0, 0, 0, 0, 0};   // CalSet: xs ys h panTrim tiltTrim
};
struct ParseResult { ParseError err = ParseError::None; Command cmd; };

constexpr unsigned MAX_LINE = 64;

// Tolerante con espacios, \r\n y mayúsculas/minúsculas. "(x,y)" EXIGE paréntesis; x,y enteros en 1..cfg::GRID_N.
//   "(12,7)" / "( 12 , 7 )" → Fire;  "TEST","STOP","PING","CAL SHOW","CAL SET a b c d e","CAL SAVE","CAL RESET","MARK HIT","MARK MISS".
// Errores: línea vacía → Empty; > MAX_LINE → TooLong; "(a,b)" no numérico o sintaxis mala → BadFormat;
// enteros fuera de 1..GRID_N → Range; palabra desconocida → Unknown. CAL SET exige 5 números → si no, BadFormat.
ParseResult parseLine(const std::string& line);

std::string errorText(ParseError e);          // "ERR EMPTY" | "ERR TOOLONG" | "ERR FORMAT" | "ERR RANGE" | "ERR UNKNOWN" ("" si None)
std::string fireOkText(int x, int y);         // "OK (x,y)"

}  // namespace core
