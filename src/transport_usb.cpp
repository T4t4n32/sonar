#include "transport_usb.h"
#include <Arduino.h>

namespace transport {

void UsbTransport::begin(unsigned long baud) {
  Serial.begin(baud);
}

bool UsbTransport::readLine(std::string& out) {
  while (Serial.available() > 0) {
    const int c = Serial.read();
    if (c < 0) break;
    if (assembler_.feed((uint8_t)c, out)) return true;   // una línea por llamada: el resto queda en el búfer
  }
  return false;
}

void UsbTransport::writeLine(const std::string& line) {
  std::string msg = line;
  msg.push_back('\n');
  Serial.write(reinterpret_cast<const uint8_t*>(msg.data()), msg.size());   // una sola escritura por línea
}

}  // namespace transport
