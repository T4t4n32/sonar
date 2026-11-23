#include "transport_bt.h"
#include <Arduino.h>

namespace transport {

bool BtTransport::begin(const char* name) {
  return serial_.begin(name);
}

bool BtTransport::readLine(std::string& out) {
  while (serial_.available() > 0) {
    const int c = serial_.read();
    if (c < 0) break;
    if (assembler_.feed((uint8_t)c, out, millis())) return true;
  }
  return assembler_.flushIdle(out, millis());   // apps que no mandan salto de línea: "TEST" suelto se entrega a los 300 ms
}

void BtTransport::writeLine(const std::string& line) {
  if (!serial_.hasClient()) return;
  std::string msg = line;
  msg.push_back('\n');
  // BluetoothSerial copia el mensaje a una cola y lo envía desde su propia tarea: no bloquea.
  serial_.write(reinterpret_cast<const uint8_t*>(msg.data()), msg.size());
}

}  // namespace transport
