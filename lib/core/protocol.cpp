// Analizador del protocolo de líneas de texto (docs/PROTOCOLO.md). PURO C++ (sin Arduino).
#include "protocol.h"

#include <stdio.h>
#include <stdlib.h>

#include <vector>

#include "config.h"

namespace core {

namespace {

bool isBlank(char c) { return c == ' ' || c == '\t'; }
bool isTrim(char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; }
bool isDigit(char c) { return c >= '0' && c <= '9'; }
bool isAlpha(char c) { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'); }
char upper(char c) { return (c >= 'a' && c <= 'z') ? static_cast<char>(c - 'a' + 'A') : c; }

ParseResult failure(ParseError e) {
  ParseResult r;
  r.err = e;
  return r;
}

// "(x,y)" ya sin espacios en los extremos; s[0] == '('. Los errores de sintaxis ganan a los de rango.
ParseResult parseFire(const std::string& s) {
  const size_t n = s.size();
  size_t i = 1;
  long vals[2] = {0, 0};
  for (int k = 0; k < 2; ++k) {
    while (i < n && isBlank(s[i])) ++i;
    bool neg = false;
    if (i < n && (s[i] == '+' || s[i] == '-')) {
      neg = (s[i] == '-');
      ++i;
    }
    if (i >= n || !isDigit(s[i])) return failure(ParseError::BadFormat);
    long v = 0;
    while (i < n && isDigit(s[i])) {
      if (v < 1000000) v = v * 10 + (s[i] - '0');   // tope: los enteros enormes acaban en Range, sin desbordar
      ++i;
    }
    vals[k] = neg ? -v : v;
    while (i < n && isBlank(s[i])) ++i;
    const char expected = (k == 0) ? ',' : ')';
    if (i >= n || s[i] != expected) return failure(ParseError::BadFormat);
    ++i;
  }
  if (i != n) return failure(ParseError::BadFormat);   // basura tras el ')'

  if (vals[0] < 1 || vals[0] > cfg::GRID_N || vals[1] < 1 || vals[1] > cfg::GRID_N) return failure(ParseError::Range);

  ParseResult r;
  r.cmd.type = CmdType::Fire;
  r.cmd.x = static_cast<int>(vals[0]);
  r.cmd.y = static_cast<int>(vals[1]);
  return r;
}

// Número decimal estricto: [+-] dígitos [. dígitos] | [+-] . dígitos. Sin exponente, "nan" ni "inf".
bool parseNumber(const std::string& t, float& out) {
  size_t i = 0;
  const size_t n = t.size();
  if (i < n && (t[i] == '+' || t[i] == '-')) ++i;
  size_t digits = 0;
  while (i < n && isDigit(t[i])) { ++i; ++digits; }
  if (i < n && t[i] == '.') {
    ++i;
    while (i < n && isDigit(t[i])) { ++i; ++digits; }
  }
  if (digits == 0 || i != n) return false;
  out = static_cast<float>(strtod(t.c_str(), nullptr));
  return true;
}

std::vector<std::string> tokenize(const std::string& s, bool upperCase) {
  std::vector<std::string> tokens;
  std::string cur;
  for (size_t i = 0; i < s.size(); ++i) {
    if (isBlank(s[i])) {
      if (!cur.empty()) { tokens.push_back(cur); cur.clear(); }
    } else {
      cur.push_back(upperCase ? upper(s[i]) : s[i]);
    }
  }
  if (!cur.empty()) tokens.push_back(cur);
  return tokens;
}

ParseResult simple(CmdType t) {
  ParseResult r;
  r.cmd.type = t;
  return r;
}

ParseResult parseKeyword(const std::string& s) {
  const std::vector<std::string> tok = tokenize(s, true);
  const std::string& w = tok[0];   // s no está vacío y empieza por letra: hay al menos un token

  if (w == "TEST" || w == "STOP" || w == "PING") {
    if (tok.size() != 1) return failure(ParseError::BadFormat);
    return simple(w == "TEST" ? CmdType::Test : (w == "STOP" ? CmdType::Stop : CmdType::Ping));
  }

  if (w == "MARK") {
    if (tok.size() < 2) return failure(ParseError::BadFormat);
    if (tok[1] != "HIT" && tok[1] != "MISS") return failure(ParseError::Unknown);
    if (tok.size() != 2) return failure(ParseError::BadFormat);
    return simple(tok[1] == "HIT" ? CmdType::MarkHit : CmdType::MarkMiss);
  }

  if (w == "CAL") {
    if (tok.size() < 2) return failure(ParseError::BadFormat);
    const std::string& sub = tok[1];
    if (sub == "SHOW" || sub == "SAVE" || sub == "RESET") {
      if (tok.size() != 2) return failure(ParseError::BadFormat);
      return simple(sub == "SHOW" ? CmdType::CalShow : (sub == "SAVE" ? CmdType::CalSave : CmdType::CalReset));
    }
    if (sub == "SET") {
      if (tok.size() != 7) return failure(ParseError::BadFormat);   // CAL SET + exactamente 5 números
      ParseResult r = simple(CmdType::CalSet);
      for (int k = 0; k < 5; ++k) {
        if (!parseNumber(tok[2 + k], r.cmd.cal[k])) return failure(ParseError::BadFormat);
      }
      return r;
    }
    return failure(ParseError::Unknown);
  }

  return failure(ParseError::Unknown);
}

}  // namespace

ParseResult parseLine(const std::string& line) {
  // Se descarta el fin de línea (\r\n) antes de medir: la longitud máxima es la del contenido.
  size_t end = line.size();
  while (end > 0 && (line[end - 1] == '\r' || line[end - 1] == '\n')) --end;
  if (end > MAX_LINE) return failure(ParseError::TooLong);

  size_t b = 0;
  while (b < end && isTrim(line[b])) ++b;
  while (end > b && isTrim(line[end - 1])) --end;
  if (b == end) return failure(ParseError::Empty);

  const std::string s = line.substr(b, end - b);
  if (s[0] == '(') return parseFire(s);
  if (isAlpha(s[0])) return parseKeyword(s);
  return failure(ParseError::BadFormat);   // empieza por dígito o símbolo ("12,7", "-3", ...): intento de coordenada mal escrito
}

std::string errorText(ParseError e) {
  switch (e) {
    case ParseError::Empty:     return "ERR EMPTY";
    case ParseError::TooLong:   return "ERR TOOLONG";
    case ParseError::BadFormat: return "ERR FORMAT";
    case ParseError::Range:     return "ERR RANGE";
    case ParseError::Unknown:   return "ERR UNKNOWN";
    case ParseError::None:      break;
  }
  return "";
}

std::string fireOkText(int x, int y) {
  char buf[40];
  snprintf(buf, sizeof buf, "OK (%d,%d)", x, y);
  return buf;
}

}  // namespace core
