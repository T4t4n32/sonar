#pragma once
// Transporte USB: el puerto serie del monitor (UART0 vía el puente USB-serie de la placa), 115200 8N1.
#include "line_transport.h"

namespace transport {

class UsbTransport : public LineTransport {
 public:
  void begin(unsigned long baud = 115200);
  bool readLine(std::string& out) override;
  void writeLine(const std::string& line) override;

 private:
  LineAssembler assembler_;
};

}  // namespace transport
