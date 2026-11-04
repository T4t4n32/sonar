#include "transport_wifi.h"
#include <WiFi.h>
#include "line_transport.h"

// web/index.html embebido por board_build.embed_txtfiles (PlatformIO añade un NUL final).
extern const uint8_t kIndexStart[] asm("_binary_web_index_html_start");
extern const uint8_t kIndexEnd[] asm("_binary_web_index_html_end");

namespace transport {

WifiMaint::~WifiMaint() = default;

bool WifiMaint::begin(const char* ssid, const char* password, Handler handler) {
  handler_ = std::move(handler);
  WiFi.mode(WIFI_AP);
  if (!WiFi.softAP(ssid, password)) return false;   // 192.168.4.1 por defecto
  server_.reset(new WebServer(80));
  server_->on("/", HTTP_GET, [this]() { sendIndex(); });
  server_->on("/cmd", HTTP_GET, [this]() { handleCmd(); });
  server_->on("/favicon.ico", HTTP_GET, [this]() { server_->send(204); });
  server_->onNotFound([this]() { server_->send(404, "text/plain", "ERR NOTFOUND\n"); });
  server_->begin();
  return true;
}

void WifiMaint::poll() {
  if (server_) server_->handleClient();
}

void WifiMaint::sendIndex() {
  size_t len = (size_t)(kIndexEnd - kIndexStart);
  if (len > 0 && kIndexStart[len - 1] == 0) --len;   // sin el NUL terminador
  server_->send_P(200, "text/html; charset=utf-8", reinterpret_cast<PGM_P>(kIndexStart), len);
}

void WifiMaint::handleCmd() {
  // WebServer ya decodifica %XX y '+'. Sin parámetro `l` resulta una línea vacía → ERR EMPTY.
  const std::string line = sanitizeLine(server_->arg("l").c_str());
  std::string body;
  handler_(line, [&body](const std::string& s) {
    body += s;
    body += '\n';
  });
  server_->sendHeader("Cache-Control", "no-store");   // nunca reutilizar una respuesta (p. ej. dos PING seguidos)
  server_->send(200, "text/plain; charset=utf-8", body.c_str());
}

}  // namespace transport
