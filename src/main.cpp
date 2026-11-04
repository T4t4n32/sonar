// duelo-laser: firmware de un módulo (el MISMO programa en A y B; el nombre sale de DEVICE_NAME).
//
// Dos modos, elegidos UNA vez al arrancar leyendo el pin MAINT:
//   Juego          (MAINT abierto): Bluetooth SPP (DEVICE_NAME) + USB. El Wi-Fi no se inicia.
//   Mantenimiento  (MAINT a GND)  : Wi-Fi AP (WIFI_SSID_MAINT) + servidor web + USB. El Bluetooth no se inicia.
// El controlador (lib/core) no sabe nada de transportes: recibe una línea y entrega respuestas por un callback.
//
// STOP durante un disparo: Controller::handleLine bloquea hasta terminar, pero toda su espera pasa por
// ArduinoClock::delayMs, que llama a idleHook() cada ~2 ms. El gancho lee los canales de línea (BT/USB):
// un STOP apaga el láser y llama a requestStop(); cualquier otra línea se responde ERR BUSY.
#include <Arduino.h>
#include <string>
#include "config.h"
#include "controller.h"
#include "hal_esp32.h"
#include "line_transport.h"
#include "protocol.h"
#include "transport_bt.h"
#include "transport_usb.h"
#include "transport_wifi.h"

// ---------------------------------------------------------------------------------------------------------------
// Hardware. El láser va PRIMERO: su constructor lo deja en LOW durante la inicialización estática, antes de setup().
static hal_esp32::LaserPin g_laser(cfg::pins::LASER);
static hal_esp32::ArduinoClock g_clock;
static hal_esp32::LedcServo g_pan(cfg::pins::PAN, 0);     // canales 0 y 2: temporizadores LEDC distintos
static hal_esp32::LedcServo g_tilt(cfg::pins::TILT, 2);
static hal_esp32::ActiveBuzzer g_buzzer(cfg::pins::BUZZER, g_clock);
static hal_esp32::LedPin g_led(cfg::pins::LED);
static hal_esp32::NvsCalStore g_store;
static core::Controller g_ctrl(g_pan, g_tilt, g_laser, g_buzzer, g_led, g_clock, g_store);

// Transportes.
static transport::UsbTransport g_usb;
static transport::BtTransport g_bt;
static transport::WifiMaint g_wifi;

// Canales de línea activos en este modo (BT+USB en juego, solo USB en mantenimiento).
static transport::LineTransport* g_links[2] = {nullptr, nullptr};
static size_t g_linkCount = 0;
static bool g_maintMode = false;

// true mientras Controller::handleLine está ejecutándose (de ahí en adelante, el reloj llama al gancho).
static volatile bool g_handling = false;

// Estado del pulsador TEST (antirrebote por tiempo).
static bool g_btnStable = true;      // true = suelto (INPUT_PULLUP → HIGH)
static bool g_btnLastRaw = true;
static uint32_t g_btnSince = 0;
constexpr uint32_t kDebounceMs = 30;

// ---------------------------------------------------------------------------------------------------------------
static void execute(const std::string& line, const core::Controller::Reply& reply) {
  g_handling = true;
  g_ctrl.handleLine(line, reply);
  g_handling = false;
}

// Llamado por el reloj cada ~2 ms mientras el controlador espera. Solo actúa durante handleLine.
static void idleHook() {
  if (!g_handling) return;
  for (size_t i = 0; i < g_linkCount; ++i) {          // una línea por canal y llamada; la siguiente, en 2 ms
    std::string line;
    if (!g_links[i]->readLine(line)) continue;
    const core::ParseResult r = core::parseLine(line);
    if (r.err == core::ParseError::None && r.cmd.type == core::CmdType::Stop) {
      g_laser.set(false);                             // apagado inmediato, sin esperar al controlador
      g_ctrl.requestStop();                           // el disparo en curso responderá ERR STOP
      g_links[i]->writeLine("OK STOP");
    } else {
      g_links[i]->writeLine("ERR BUSY");
    }
  }
}

// ¿Está el interruptor MAINT a GND? Se muestrea varias veces para ignorar un contacto dudoso.
static bool maintRequested() {
  pinMode(cfg::pins::MAINT, INPUT_PULLUP);
  delay(20);                                          // deja cargar el pull-up interno
  int low = 0;
  for (int i = 0; i < 9; ++i) {
    if (digitalRead(cfg::pins::MAINT) == LOW) ++low;
    delay(2);
  }
  return low >= 5;
}

static void pollButton() {
  const bool raw = digitalRead(cfg::pins::BTN_TEST) != LOW;
  const uint32_t now = millis();
  if (raw != g_btnLastRaw) {
    g_btnLastRaw = raw;
    g_btnSince = now;
    return;
  }
  if (raw == g_btnStable || (now - g_btnSince) < kDebounceMs) return;
  g_btnStable = raw;
  if (!raw) {                                         // flanco de bajada confirmado: pulsado
    execute("TEST", [](const std::string& s) { g_usb.writeLine(s); });   // el resultado se ve por el monitor USB
    g_btnLastRaw = g_btnStable = digitalRead(cfg::pins::BTN_TEST) != LOW; // si sigue pulsado, exige soltar y pulsar
    g_btnSince = millis();
  }
}

// ---------------------------------------------------------------------------------------------------------------
void setup() {
  g_laser.set(false);                                 // redundante con el constructor; no cuesta nada
  g_usb.begin(115200);

  pinMode(cfg::pins::BTN_TEST, INPUT_PULLUP);
  g_maintMode = maintRequested();
  g_btnStable = g_btnLastRaw = digitalRead(cfg::pins::BTN_TEST) != LOW;
  g_btnSince = millis();

  g_clock.setIdleHook(idleHook);
  g_ctrl.begin();                                     // láser apagado, calibración cargada, servos libres

  g_links[g_linkCount++] = &g_usb;
  if (g_maintMode) {
    // Mantenimiento: Wi-Fi sí, Bluetooth no (nunca se llama a g_bt.begin()).
    g_wifi.begin(WIFI_SSID_MAINT, WIFI_PASS_MAINT,
                 [](const std::string& line, const transport::WifiMaint::Reply& reply) { execute(line, reply); });
  } else {
    // Juego: Bluetooth sí, Wi-Fi no (nunca se toca el objeto WiFi). Si el BT falla, el USB sigue sirviendo.
    if (g_bt.begin(DEVICE_NAME)) g_links[g_linkCount++] = &g_bt;
  }
}

void loop() {
  if (g_maintMode) g_wifi.poll();

  for (size_t i = 0; i < g_linkCount; ++i) {
    transport::LineTransport* link = g_links[i];
    std::string line;
    if (link->readLine(line)) {
      execute(line, [link](const std::string& s) { link->writeLine(s); });   // la respuesta vuelve por el mismo canal
    }
  }

  pollButton();
  delay(1);                                           // cede la CPU a las tareas de BT / Wi-Fi
}
