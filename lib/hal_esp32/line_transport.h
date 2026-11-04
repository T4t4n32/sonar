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
class LineAssembler {
 public:
  // Alimenta un byte; true si con él se completó una línea (queda en `out`).
  bool feed(uint8_t c, std::string& out) {
    if (c == '\r') return false;
    if (c == '\n') {
      out.swap(buf_);
      buf_.clear();
      return true;
    }
    if (buf_.size() < kMaxRetained) buf_.push_back((char)c);
    return false;
  }

 private:
  std::string buf_;
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
