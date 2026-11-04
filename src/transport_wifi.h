#pragma once
// Transporte Wi-Fi de mantenimiento: punto de acceso + servidor HTTP.
//   GET /            → la interfaz web (web/index.html, embebida en el firmware)
//   GET /cmd?l=LINEA → ejecuta la línea y responde en text/plain, una línea por respuesta.
// HTTP es petición/respuesta, así que no implementa LineTransport: recibe un manejador que ejecuta la línea.
//
// LIMITACIÓN: el servidor atiende una petición a la vez en el hilo principal, y un disparo bloquea hasta
// terminar (~2 s; TEST ~12 s). Mientras tanto no se atiende ninguna otra petición HTTP, así que un STOP por
// Wi-Fi solo llega al terminar. El STOP durante un disparo funciona por USB (también activo en este modo).
#include <WebServer.h>
#include <functional>
#include <memory>
#include <string>

namespace transport {

class WifiMaint {
 public:
  using Reply = std::function<void(const std::string&)>;
  using Handler = std::function<void(const std::string& line, const Reply& reply)>;

  ~WifiMaint();
  // Levanta la red `ssid` y el servidor. false si el punto de acceso no arrancó.
  bool begin(const char* ssid, const char* password, Handler handler);
  void poll();   // atiende las peticiones pendientes; llamar en cada vuelta de loop()

 private:
  std::unique_ptr<WebServer> server_;
  Handler handler_;
  void sendIndex();
  void handleCmd();
};

}  // namespace transport
