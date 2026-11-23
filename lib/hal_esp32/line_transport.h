#pragma once
// Interfaz común de los transportes de texto por líneas (Bluetooth, USB) y el ensamblador de líneas.
// Vive junto al HAL porque src/ solo debe contener main.cpp y los transportes concretos.
#include <stddef.h>
#include <stdint.h>
#include <string>
#include "protocol.h"   // core::MAX_LINE

namespace transport {

// Un canal por el que llegan órdenes y salen respuestas, una línea por mensaje (terminadas en '\n').
struct LineTransport {
  virtual ~LineTransport() {}
  // No bloquea. true si `out` recibió una línea completa (sin '\n' ni '\r'); false si aún no hay ninguna.
  virtual bool readLine(std::string& out) = 0;
  // Envía `line` + '\n'. Si no hay nadie conectado, descarta en silencio.
  virtual void writeLine(const std::string& line) = 0;
};

// Longitud máxima que se retiene de una línea: MAX_LINE + margen. Una línea más larga se recorta a este tamaño
// (siempre > MAX_LINE, así el controlador responde ERR TOOLONG) y el resto se descarta hasta el '\n':
// ni desborda la RAM ni deja basura pegada a la línea siguiente.
constexpr size_t kMaxRetained = core::MAX_LINE + 16;

// Convierte un flujo de bytes en líneas. Ignora '\r' (tolera \r\n) y termina la línea en '\n'.
//
// Además es tolerante con las apps del rival (nos manejan por Bluetooth con la suya, que no sabemos cómo envía):
//  - "(x,y)" se entrega al llegar el ')' aunque la app no mande salto de línea; el '\r'/'\n' que lo siga se descarta
//    (no genera una línea vacía ni un "ERR EMPTY" de más);
//  - flushIdle(): una línea sin terminador que lleva > kIdleFlushMs quieta se entrega si es una orden válida ("TEST", "PING"...).
class LineAssembler {
 public:
  static constexpr uint32_t kIdleFlushMs = 300;

  // Alimenta un byte; true si con él se completó una línea (queda en `out`). `nowMs` solo se usa para flushIdle().
  bool feed(uint8_t c, std::string& out, uint32_t nowMs = 0) {
    lastMs_ = nowMs;
    if (c == '\r' || c == '\n') {
      if (skipEol_) {                 // la línea ya salió al llegar el ')': el salto que la sigue sobra
        if (c == '\n') skipEol_ = false;
        return false;
      }
      if (c == '\r') return false;
      out.swap(buf_);
      buf_.clear();
      return true;
    }
    skipEol_ = false;
    if (buf_.size() < kMaxRetained) buf_.push_back((char)c);
    if (c == ')' && looksLikeShot(buf_)) {
      out.swap(buf_);
      buf_.clear();
      skipEol_ = true;
      return true;
    }
    return false;
  }

  // Entrega una línea sin terminador que lleva quieta kIdleFlushMs, solo si es una orden que el protocolo entiende.
  bool flushIdle(std::string& out, uint32_t nowMs) {
    if (buf_.empty() || static_cast<uint32_t>(nowMs - lastMs_) < kIdleFlushMs) return false;
    if (core::parseLine(buf_).err != core::ParseError::None) return false;
    out.swap(buf_);
    buf_.clear();
    skipEol_ = true;
    return true;
  }

 private:
  // "(", dígitos / espacios / signo, una sola coma, ")" y nada más (con espacios alrededor).
  static bool looksLikeShot(const std::string& s) {
    size_t i = 0, e = s.size();
    while (i < e && (s[i] == ' ' || s[i] == '\t')) ++i;
    if (i >= e || s[i] != '(') return false;
    ++i;
    int commas = 0;
    for (; i < e; ++i) {
      const char ch = s[i];
      if (ch == ',') { ++commas; continue; }
      if (ch == ')') break;
      if (!((ch >= '0' && ch <= '9') || ch == ' ' || ch == '\t' || ch == '+')) return false;
    }
    if (i >= e || commas != 1) return false;
    for (++i; i < e; ++i) {
      if (s[i] != ' ' && s[i] != '\t') return false;
    }
    return true;
  }

  std::string buf_;
  uint32_t lastMs_ = 0;
  bool skipEol_ = false;
};

// Para los canales que ya traen la línea entera (HTTP): quita '\r', corta en el primer '\n' y limita el tamaño.
inline std::string sanitizeLine(const char* s) {
  std::string out;
  for (; s && *s && *s != '\n' && out.size() < kMaxRetained; ++s) {
    if (*s != '\r') out.push_back(*s);
  }
  return out;
}

}  // namespace transport
