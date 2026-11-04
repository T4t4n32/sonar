#pragma once
// Transporte Bluetooth clásico (SPP) con BluetoothSerial. Solo existe en el ESP32 "clásico".
// Emparejamiento por PIN heredado: el valor por defecto del core es 1234.
#include <BluetoothSerial.h>
#include "line_transport.h"

namespace transport {

class BtTransport : public LineTransport {
 public:
  // Arranca el Bluetooth con el nombre visible `name`. false si el controlador no arrancó.
  bool begin(const char* name);
  bool readLine(std::string& out) override;
  void writeLine(const std::string& line) override;   // sin cliente conectado, descarta

 private:
  BluetoothSerial serial_;
  LineAssembler assembler_;
};

}  // namespace transport
