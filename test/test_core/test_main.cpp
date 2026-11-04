// Pruebas Unity de lib/core (protocolo, geometría, calibración y controlador) con HAL falsos.
// Se ejecutan en el PC:  pio test -e native
#include <unity.h>

#include <math.h>
#include <stdio.h>
#include <string.h>

#include <cmath>
#include <string>
#include <vector>

#include "config.h"
#include "controller.h"
#include "fakes.h"
#include "geometry.h"
#include "protocol.h"

using fakes::Ev;
using fakes::Event;
using fakes::Rig;

// Unity (C) llama a estas funciones: deben tener enlace C. PlatformIO ya aporta versiones débiles vacías.
extern "C" {
void setUp(void) {}
void tearDown(void) {}
}

// =====================================================================================================================
// Utilidades
// =====================================================================================================================

static std::string num(unsigned long v) {
  char b[32];
  snprintf(b, sizeof b, "%lu", v);
  return b;
}

static std::string f2(double v) {
  char b[40];
  snprintf(b, sizeof b, "%.2f", v);
  return b;
}

static std::string join(const std::vector<std::string>& v, const char* sep = " | ") {
  std::string s;
  for (size_t i = 0; i < v.size(); ++i) {
    if (i) s += sep;
    s += v[i];
  }
  return s;
}

static std::vector<std::string> cat(std::vector<std::string> a, const std::vector<std::string>& b) {
  a.insert(a.end(), b.begin(), b.end());
  return a;
}

// Compara dos listas de textos; al fallar, Unity imprime ambas completas (una por línea).
#define EXPECT_TOKENS(expected, got) TEST_ASSERT_EQUAL_STRING(join((expected), "\n").c_str(), join((got), "\n").c_str())
#define EXPECT_REPLIES(got, ...)                                         \
  do {                                                                   \
    const std::vector<std::string> expectedReplies_ = {__VA_ARGS__};     \
    EXPECT_TOKENS(expectedReplies_, (got));                              \
  } while (0)

static const char* servoName(int id) { return id == 0 ? "pan" : "tilt"; }

static size_t mark(const Rig& r) { return r.log.events.size(); }

static int countKind(const Rig& r, Ev kind) {
  int n = 0;
  for (const Event& e : r.log.events) {
    if (e.kind == kind) ++n;
  }
  return n;
}

static int countLaserOn(const Rig& r) {
  int n = 0;
  for (const Event& e : r.log.events) {
    if (e.kind == Ev::LaserSet && e.on) ++n;
  }
  return n;
}

// Describe los eventos desde `from` como una lista de textos legible. Las rampas (escritura de servo seguida de
// delayMs(STEP_MS)) se agrupan por servo y sentido:  "MOVE pan up n=24 end=136.62".  Una escritura suelta (sin esa
// espera) es  "W pan 90.00".  Las respuestas aparecen como  "REPLY <texto>".
static std::vector<std::string> describe(const Rig& r, size_t from) {
  struct Tok {
    std::string text;
    bool move = false;
    int servo = 0;
    bool up = false;
    int n = 0;
    float end = 0.0f;
  };
  std::vector<Tok> toks;
  float last[2] = {NAN, NAN};
  const std::vector<Event>& ev = r.log.events;

  for (size_t i = 0; i < ev.size(); ++i) {
    const Event& e = ev[i];
    const bool emit = (i >= from);
    switch (e.kind) {
      case Ev::ServoWrite: {
        const bool ramp = (i + 1 < ev.size()) && ev[i + 1].kind == Ev::Delay && ev[i + 1].ms == cfg::STEP_MS;
        const bool up = !(e.deg < last[e.servo]);
        last[e.servo] = e.deg;
        if (ramp) {
          if (emit) {
            if (!toks.empty() && toks.back().move && toks.back().servo == e.servo && toks.back().up == up) {
              ++toks.back().n;
              toks.back().end = e.deg;
            } else {
              Tok t;
              t.move = true;
              t.servo = e.servo;
              t.up = up;
              t.n = 1;
              t.end = e.deg;
              toks.push_back(t);
            }
          }
          ++i;   // la espera de la rampa ya está contada
        } else if (emit) {
          Tok t;
          t.text = std::string("W ") + servoName(e.servo) + " " + f2(e.deg);
          toks.push_back(t);
        }
        break;
      }
      default: {
        if (!emit) break;
        Tok t;
        switch (e.kind) {
          case Ev::ServoAttach: t.text = std::string("ATTACH ") + servoName(e.servo); break;
          case Ev::ServoDetach: t.text = std::string("DETACH ") + servoName(e.servo); break;
          case Ev::LaserSet:    t.text = std::string("LASER ") + (e.on ? "1" : "0"); break;
          case Ev::Delay:       t.text = "DELAY " + num(e.ms); break;
          case Ev::Beep:        t.text = "BEEP " + num(e.hz) + " " + num(e.ms); break;
          case Ev::LedSet:      t.text = std::string("LED ") + (e.on ? "1" : "0"); break;
          case Ev::StoreLoad:   t.text = "STORE LOAD"; break;
          case Ev::StoreSave:   t.text = "STORE SAVE"; break;
          case Ev::StoreErase:  t.text = "STORE ERASE"; break;
          case Ev::Reply:       t.text = "REPLY " + e.text; break;
          default: break;
        }
        toks.push_back(t);
        break;
      }
    }
  }

  std::vector<std::string> out;
  for (const Tok& t : toks) {
    if (t.move) {
      out.push_back(std::string("MOVE ") + servoName(t.servo) + (t.up ? " up" : " down") + " n=" + num((unsigned long)t.n) +
                    " end=" + f2(t.end));
    } else {
      out.push_back(t.text);
    }
  }
  return out;
}

// Cola común de un disparo válido a partir del fin de la última rampa.
static std::vector<std::string> shotTail(int x, int y) {
  return {"DELAY " + num(cfg::SETTLE_MS),
          "LASER 1",
          "BEEP " + num(cfg::BEEP_HZ) + " " + num(cfg::BEEP_MS),
          "DELAY " + num(cfg::LASER_ON_MS),
          "LASER 0",
          "REPLY OK (" + num((unsigned long)x) + "," + num((unsigned long)y) + ")"};
}

// Invariantes de seguridad sobre TODO el registro de un módulo:
//  - ninguna escritura / attach / detach de servo con el láser encendido,
//  - servos solo escritos estando activos y dentro de 0..180,
//  - pasos de rampa <= MAX_STEP_DEG entre escrituras consecutivas del mismo servo,
//  - láser apagado al final.
static void checkSafety(const Rig& r) {
  float last[2] = {NAN, NAN};
  for (size_t i = 0; i < r.log.events.size(); ++i) {
    const Event& e = r.log.events[i];
    char msg[96];
    if (e.kind == Ev::ServoWrite || e.kind == Ev::ServoAttach || e.kind == Ev::ServoDetach) {
      snprintf(msg, sizeof msg, "LASER ENCENDIDO durante actividad de servo (evento %u)", (unsigned)i);
      TEST_ASSERT_FALSE_MESSAGE(e.laserOn, msg);
    }
    if (e.kind == Ev::ServoWrite) {
      snprintf(msg, sizeof msg, "paso de rampa > MAX_STEP_DEG (evento %u)", (unsigned)i);
      if (!std::isnan(last[e.servo])) {
        TEST_ASSERT_TRUE_MESSAGE(std::fabs(e.deg - last[e.servo]) <= cfg::MAX_STEP_DEG + 1e-3f, msg);
      }
      last[e.servo] = e.deg;
    }
  }
  TEST_ASSERT_FALSE_MESSAGE(r.log.laserOn, "el laser debe quedar apagado");
  TEST_ASSERT_EQUAL_INT(0, r.pan.writesWhileDetached);
  TEST_ASSERT_EQUAL_INT(0, r.tilt.writesWhileDetached);
  TEST_ASSERT_EQUAL_INT(0, r.pan.writesOutOfRange);
  TEST_ASSERT_EQUAL_INT(0, r.tilt.writesOutOfRange);
}

static void expectCal(const core::Calibration& c, float x, float y, float h, float pt, float tt) {
  TEST_ASSERT_EQUAL_FLOAT(x, c.station.xMm);
  TEST_ASSERT_EQUAL_FLOAT(y, c.station.yMm);
  TEST_ASSERT_EQUAL_FLOAT(h, c.station.hMm);
  TEST_ASSERT_EQUAL_FLOAT(pt, c.panTrimDeg);
  TEST_ASSERT_EQUAL_FLOAT(tt, c.tiltTrimDeg);
}

static void expectDefaultCal(const core::Calibration& c) {
  expectCal(c, cfg::STATION_X_MM, cfg::STATION_Y_MM, cfg::TILT_H_MM, 0.0f, 0.0f);
}

// =====================================================================================================================
// 1. Analizador del protocolo
// =====================================================================================================================

static void expectErr(const std::string& line, core::ParseError e) {
  const core::ParseResult r = core::parseLine(line);
  TEST_ASSERT_EQUAL_INT_MESSAGE(static_cast<int>(e), static_cast<int>(r.err), line.c_str());
}

static void expectType(const std::string& line, core::CmdType t) {
  const core::ParseResult r = core::parseLine(line);
  TEST_ASSERT_EQUAL_INT_MESSAGE(static_cast<int>(core::ParseError::None), static_cast<int>(r.err), line.c_str());
  TEST_ASSERT_EQUAL_INT_MESSAGE(static_cast<int>(t), static_cast<int>(r.cmd.type), line.c_str());
}

static void test_parse_fire_valid(void) {
  struct Case { const char* line; int x; int y; };
  const Case cases[] = {
      {"(12,7)", 12, 7},        {"( 12 , 7 )", 12, 7},     {"(1,1)", 1, 1},          {"(20,20)", 20, 20},
      {"(12,7)\r\n", 12, 7},    {"(12,7)\n", 12, 7},       {"( 12 , 7 )\r\n", 12, 7}, {"  (3,4)  ", 3, 4},
      {"\t(3,\t4)", 3, 4},      {"(05,6)", 5, 6},          {"(+5,6)", 5, 6},         {"(1,20)", 1, 20},
      {"(20,1)", 20, 1},
  };
  for (const Case& c : cases) {
    const core::ParseResult r = core::parseLine(c.line);
    TEST_ASSERT_EQUAL_INT_MESSAGE(static_cast<int>(core::ParseError::None), static_cast<int>(r.err), c.line);
    TEST_ASSERT_EQUAL_INT_MESSAGE(static_cast<int>(core::CmdType::Fire), static_cast<int>(r.cmd.type), c.line);
    TEST_ASSERT_EQUAL_INT_MESSAGE(c.x, r.cmd.x, c.line);
    TEST_ASSERT_EQUAL_INT_MESSAGE(c.y, r.cmd.y, c.line);
  }
}

static void test_parse_keywords(void) {
  expectType("test", core::CmdType::Test);
  expectType("TEST", core::CmdType::Test);
  expectType("STOP", core::CmdType::Stop);
  expectType("Ping", core::CmdType::Ping);
  expectType("ping\r\n", core::CmdType::Ping);
  expectType("  PING  ", core::CmdType::Ping);
  expectType("cal show", core::CmdType::CalShow);
  expectType("CAL SHOW\r\n", core::CmdType::CalShow);
  expectType("CAL  SHOW", core::CmdType::CalShow);
  expectType("CAL SAVE", core::CmdType::CalSave);
  expectType("Cal Reset", core::CmdType::CalReset);
  expectType("MARK HIT", core::CmdType::MarkHit);
  expectType("MARK HIT\r\n", core::CmdType::MarkHit);
  expectType("mark miss", core::CmdType::MarkMiss);
  expectType("MARK MISS\n", core::CmdType::MarkMiss);
}

static void test_parse_cal_set(void) {
  core::ParseResult r = core::parseLine("cal set 100 -65 180 0 0");
  TEST_ASSERT_EQUAL_INT(static_cast<int>(core::ParseError::None), static_cast<int>(r.err));
  TEST_ASSERT_EQUAL_INT(static_cast<int>(core::CmdType::CalSet), static_cast<int>(r.cmd.type));
  const float e1[5] = {100.0f, -65.0f, 180.0f, 0.0f, 0.0f};
  for (int i = 0; i < 5; ++i) TEST_ASSERT_EQUAL_FLOAT(e1[i], r.cmd.cal[i]);

  r = core::parseLine("CAL SET 105.5 -60 170.25 1.5 -2\r\n");
  TEST_ASSERT_EQUAL_INT(static_cast<int>(core::ParseError::None), static_cast<int>(r.err));
  TEST_ASSERT_EQUAL_INT(static_cast<int>(core::CmdType::CalSet), static_cast<int>(r.cmd.type));
  const float e2[5] = {105.5f, -60.0f, 170.25f, 1.5f, -2.0f};
  for (int i = 0; i < 5; ++i) TEST_ASSERT_EQUAL_FLOAT(e2[i], r.cmd.cal[i]);

  // Signo explícito y fracción sin parte entera.
  r = core::parseLine("CAL SET +100 -65.5 .5 -.25 +0");
  TEST_ASSERT_EQUAL_INT(static_cast<int>(core::ParseError::None), static_cast<int>(r.err));
  const float e3[5] = {100.0f, -65.5f, 0.5f, -0.25f, 0.0f};
  for (int i = 0; i < 5; ++i) TEST_ASSERT_EQUAL_FLOAT(e3[i], r.cmd.cal[i]);
}

static void test_parse_range_errors(void) {
  expectErr("(0,5)", core::ParseError::Range);
  expectErr("(21,1)", core::ParseError::Range);
  expectErr("(1,21)", core::ParseError::Range);
  expectErr("(5,0)", core::ParseError::Range);
  expectErr("(-1,5)", core::ParseError::Range);
  expectErr("(0,0)", core::ParseError::Range);
  expectErr("(99999999999999,1)", core::ParseError::Range);
  expectErr("(1,99999999999999999999)", core::ParseError::Range);
  expectErr("(100,100)\r\n", core::ParseError::Range);
}

static void test_parse_bad_format(void) {
  expectErr("(a,b)", core::ParseError::BadFormat);
  expectErr("12,7", core::ParseError::BadFormat);
  expectErr("(12;7)", core::ParseError::BadFormat);
  expectErr("(12,7", core::ParseError::BadFormat);
  expectErr("(3,)", core::ParseError::BadFormat);
  expectErr("(,3)", core::ParseError::BadFormat);
  expectErr("()", core::ParseError::BadFormat);
  expectErr("(", core::ParseError::BadFormat);
  expectErr("(1.5,2)", core::ParseError::BadFormat);
  expectErr("(1 2,3)", core::ParseError::BadFormat);
  expectErr("(1,2,3)", core::ParseError::BadFormat);
  expectErr("(1,2)x", core::ParseError::BadFormat);
  expectErr("(1,2)(3,4)", core::ParseError::BadFormat);
  expectErr("12 7", core::ParseError::BadFormat);
  expectErr("1,7)", core::ParseError::BadFormat);
  // Un error de sintaxis gana a uno de rango.
  expectErr("(0,a)", core::ParseError::BadFormat);
  // CAL SET exige exactamente 5 números.
  expectErr("CAL SET 1 2", core::ParseError::BadFormat);
  expectErr("CAL SET", core::ParseError::BadFormat);
  expectErr("CAL SET 1 2 3 4 5 6", core::ParseError::BadFormat);
  expectErr("CAL SET a b c d e", core::ParseError::BadFormat);
  expectErr("CAL SET 1e2 2 3 4 5", core::ParseError::BadFormat);
  expectErr("CAL SET nan 2 3 4 5", core::ParseError::BadFormat);
  expectErr("CAL SET 1,5 2 3 4 5", core::ParseError::BadFormat);
  // Palabras conocidas con sobrantes o a medias.
  expectErr("CAL", core::ParseError::BadFormat);
  expectErr("CAL SHOW now", core::ParseError::BadFormat);
  expectErr("MARK", core::ParseError::BadFormat);
  expectErr("MARK HIT 1", core::ParseError::BadFormat);
  expectErr("TEST 5", core::ParseError::BadFormat);
  expectErr("PING x", core::ParseError::BadFormat);
}

static void test_parse_empty(void) {
  expectErr("", core::ParseError::Empty);
  expectErr("   ", core::ParseError::Empty);
  expectErr("\r\n", core::ParseError::Empty);
  expectErr("\n", core::ParseError::Empty);
  expectErr(" \t \r\n", core::ParseError::Empty);
}

static void test_parse_too_long(void) {
  TEST_ASSERT_EQUAL_UINT(64, core::MAX_LINE);
  // Exactamente 64 caracteres: válido. Con \r\n añadido, la longitud cuenta sin el fin de línea.
  const std::string ok64 = "(1,1)" + std::string(59, ' ');
  TEST_ASSERT_EQUAL_UINT(64, (unsigned)ok64.size());
  expectType(ok64, core::CmdType::Fire);
  expectType(ok64 + "\r\n", core::CmdType::Fire);
  // 65: demasiado larga.
  const std::string bad65 = "(1,1)" + std::string(60, ' ');
  TEST_ASSERT_EQUAL_UINT(65, (unsigned)bad65.size());
  expectErr(bad65, core::ParseError::TooLong);
  expectErr(bad65 + "\r\n", core::ParseError::TooLong);
  expectErr(std::string(65, 'A'), core::ParseError::TooLong);
  expectErr(std::string(500, '1'), core::ParseError::TooLong);
  // 64 letras: longitud válida, palabra desconocida.
  expectErr(std::string(64, 'A'), core::ParseError::Unknown);
}

static void test_parse_unknown(void) {
  expectErr("HOLA", core::ParseError::Unknown);
  expectErr("FIRE", core::ParseError::Unknown);
  expectErr("hola mundo", core::ParseError::Unknown);
  expectErr("CAL FOO", core::ParseError::Unknown);
  expectErr("MARK FOO", core::ParseError::Unknown);
  expectErr("TESTX", core::ParseError::Unknown);
}

static void test_error_and_ok_texts(void) {
  TEST_ASSERT_EQUAL_STRING("ERR EMPTY", core::errorText(core::ParseError::Empty).c_str());
  TEST_ASSERT_EQUAL_STRING("ERR TOOLONG", core::errorText(core::ParseError::TooLong).c_str());
  TEST_ASSERT_EQUAL_STRING("ERR FORMAT", core::errorText(core::ParseError::BadFormat).c_str());
  TEST_ASSERT_EQUAL_STRING("ERR RANGE", core::errorText(core::ParseError::Range).c_str());
  TEST_ASSERT_EQUAL_STRING("ERR UNKNOWN", core::errorText(core::ParseError::Unknown).c_str());
  TEST_ASSERT_EQUAL_STRING("", core::errorText(core::ParseError::None).c_str());
  TEST_ASSERT_EQUAL_STRING("OK (12,7)", core::fireOkText(12, 7).c_str());
  TEST_ASSERT_EQUAL_STRING("OK (1,20)", core::fireOkText(1, 20).c_str());
  TEST_ASSERT_EQUAL_STRING("OK (20,1)", core::fireOkText(20, 1).c_str());
}

// =====================================================================================================================
// 2. Geometría
// =====================================================================================================================

static void test_cell_in_range(void) {
  TEST_ASSERT_TRUE(core::cellInRange(1, 1));
  TEST_ASSERT_TRUE(core::cellInRange(20, 20));
  TEST_ASSERT_TRUE(core::cellInRange(1, 20));
  TEST_ASSERT_TRUE(core::cellInRange(20, 1));
  TEST_ASSERT_TRUE(core::cellInRange(10, 11));
  TEST_ASSERT_FALSE(core::cellInRange(0, 1));
  TEST_ASSERT_FALSE(core::cellInRange(1, 0));
  TEST_ASSERT_FALSE(core::cellInRange(21, 1));
  TEST_ASSERT_FALSE(core::cellInRange(1, 21));
  TEST_ASSERT_FALSE(core::cellInRange(-1, 5));
  TEST_ASSERT_FALSE(core::cellInRange(5, -1));
  TEST_ASSERT_FALSE(core::cellInRange(0, 0));
  TEST_ASSERT_FALSE(core::cellInRange(21, 21));
}

static void test_default_station_and_calibration(void) {
  const core::Station s = core::defaultStation();
  TEST_ASSERT_EQUAL_FLOAT(100.0f, s.xMm);
  TEST_ASSERT_EQUAL_FLOAT(-65.0f, s.yMm);
  TEST_ASSERT_EQUAL_FLOAT(180.0f, s.hMm);
  TEST_ASSERT_EQUAL_FLOAT(cfg::STATION_X_MM, s.xMm);
  TEST_ASSERT_EQUAL_FLOAT(cfg::STATION_Y_MM, s.yMm);
  TEST_ASSERT_EQUAL_FLOAT(cfg::TILT_H_MM, s.hMm);
  expectDefaultCal(core::defaultCalibration());
}

// Vectores esperados con la estación por defecto (xs=100, ys=-65, h=180), calculados aparte con
// pan = atan2(dx, dy), tilt = atan2(h, hypot(dx, dy)) y centro de celda (i - 0.5) * 10 mm.
static void test_aim_known_vectors(void) {
  struct Vec { int x, y; float pan, tilt; };
  const Vec vecs[] = {
      {1, 1, -53.6f, 56.8f},   {20, 1, 53.6f, 56.8f},  {20, 20, 20.1f, 33.0f}, {1, 20, -20.1f, 33.0f},
      {11, 11, 1.7f, 46.6f},   {10, 1, -4.1f, 68.7f},  {10, 20, -1.1f, 34.7f},
  };
  const core::Station s = core::defaultStation();
  for (const Vec& v : vecs) {
    char msg[40];
    snprintf(msg, sizeof msg, "celda (%d,%d)", v.x, v.y);
    const core::Aim a = core::aimAtCell(core::Cell{v.x, v.y}, s);
    TEST_ASSERT_TRUE_MESSAGE(a.ok, msg);
    TEST_ASSERT_FLOAT_WITHIN_MESSAGE(0.15f, v.pan, a.panDeg, msg);
    TEST_ASSERT_FLOAT_WITHIN_MESSAGE(0.15f, v.tilt, a.tiltDeg, msg);
  }
}

static void test_aim_all_400_cells_ok(void) {
  const core::Station s = core::defaultStation();
  for (int y = 1; y <= cfg::GRID_N; ++y) {
    for (int x = 1; x <= cfg::GRID_N; ++x) {
      char msg[40];
      snprintf(msg, sizeof msg, "celda (%d,%d)", x, y);
      const core::Aim a = core::aimAtCell(core::Cell{x, y}, s);
      TEST_ASSERT_TRUE_MESSAGE(a.ok, msg);
      TEST_ASSERT_TRUE_MESSAGE(std::fabs(a.panDeg) <= cfg::PAN_LIMIT_DEG, msg);
      TEST_ASSERT_TRUE_MESSAGE(a.tiltDeg >= cfg::TILT_MIN_DEG && a.tiltDeg <= cfg::TILT_MAX_DEG, msg);
    }
  }
}

static void test_aim_cell_out_of_range_is_not_ok(void) {
  const core::Station s = core::defaultStation();
  TEST_ASSERT_FALSE(core::aimAtCell(core::Cell{0, 5}, s).ok);
  TEST_ASSERT_FALSE(core::aimAtCell(core::Cell{21, 1}, s).ok);
  TEST_ASSERT_FALSE(core::aimAtCell(core::Cell{1, 0}, s).ok);
  TEST_ASSERT_FALSE(core::aimAtCell(core::Cell{1, 21}, s).ok);
  TEST_ASSERT_FALSE(core::aimAtCell(core::Cell{-3, -3}, s).ok);
}

static void test_aim_at_mm(void) {
  const core::Station s = core::defaultStation();
  // Un punto interior coincide con su celda: (10,1) está en (95, 5) mm.
  core::Aim a = core::aimAtMm(95.0f, 5.0f, s);
  TEST_ASSERT_TRUE(a.ok);
  TEST_ASSERT_FLOAT_WITHIN(0.15f, -4.1f, a.panDeg);
  TEST_ASSERT_FLOAT_WITHIN(0.15f, 68.7f, a.tiltDeg);

  // Directamente sobre la estación: tilt = 90° > TILT_MAX.
  TEST_ASSERT_FALSE(core::aimAtMm(100.0f, -65.0f, s).ok);
  // Muy cerca de la estación (tilt 88°) y muy lejos (tilt 2°).
  TEST_ASSERT_FALSE(core::aimAtMm(100.0f, -60.0f, s).ok);
  TEST_ASSERT_FALSE(core::aimAtMm(100.0f, 5000.0f, s).ok);
  // Detrás de la estación (pan 180°) y muy a la izquierda (pan -61°).
  TEST_ASSERT_FALSE(core::aimAtMm(100.0f, -200.0f, s).ok);
  TEST_ASSERT_FALSE(core::aimAtMm(-200.0f, 100.0f, s).ok);
  // Fuera del tablero pero dentro de los límites: aimAtMm no comprueba el rango de celdas.
  TEST_ASSERT_TRUE(core::aimAtMm(100.0f, 20.0f, s).ok);

  // Bordes del pan (y = 5 mm): 56,8° pasa, 57,3° no.
  TEST_ASSERT_TRUE(core::aimAtMm(207.0f, 5.0f, s).ok);
  TEST_ASSERT_FALSE(core::aimAtMm(209.0f, 5.0f, s).ok);
  TEST_ASSERT_FALSE(core::aimAtMm(-9.0f, 5.0f, s).ok);   // simétrico por la izquierda (pan -57,3°)
  TEST_ASSERT_TRUE(core::aimAtMm(-7.0f, 5.0f, s).ok);    // pan -56,8°
  // Bordes del tilt (x = xs): 72,14° falla (y=-7), 71,85° pasa (y=-6); 30,14° pasa (y=245), 29,90° falla (y=248).
  TEST_ASSERT_FALSE(core::aimAtMm(100.0f, -7.0f, s).ok);
  TEST_ASSERT_TRUE(core::aimAtMm(100.0f, -6.0f, s).ok);
  TEST_ASSERT_TRUE(core::aimAtMm(100.0f, 245.0f, s).ok);
  TEST_ASSERT_FALSE(core::aimAtMm(100.0f, 248.0f, s).ok);

  // Entradas no finitas nunca son ok.
  TEST_ASSERT_FALSE(core::aimAtMm(NAN, 5.0f, s).ok);
  TEST_ASSERT_FALSE(core::aimAtMm(5.0f, INFINITY, s).ok);
  core::Station bad = s;
  bad.hMm = NAN;
  TEST_ASSERT_FALSE(core::aimAtMm(95.0f, 5.0f, bad).ok);
}

static void test_aim_uses_station(void) {
  // Desplazar la estación a la izquierda corre el pan hacia la derecha.
  core::Station s = core::defaultStation();
  const core::Aim a0 = core::aimAtCell(core::Cell{11, 11}, s);
  s.xMm -= 20.0f;
  const core::Aim a1 = core::aimAtCell(core::Cell{11, 11}, s);
  TEST_ASSERT_TRUE(a0.ok && a1.ok);
  TEST_ASSERT_TRUE(a1.panDeg > a0.panDeg + 5.0f);
}

static float expectedPanServo(float panDeg, float trim) {
  float v = cfg::PAN_CENTER_SERVO_DEG + cfg::PAN_SIGN * panDeg + trim;
  return v < 0.0f ? 0.0f : (v > 180.0f ? 180.0f : v);
}
static float expectedTiltServo(float tiltDeg, float trim) {
  float v = cfg::TILT_HORIZ_SERVO_DEG + cfg::TILT_SIGN * tiltDeg + trim;
  return v < 0.0f ? 0.0f : (v > 180.0f ? 180.0f : v);
}

static void test_to_servo(void) {
  core::Calibration cal = core::defaultCalibration();

  // Rayo al frente y horizontal: el centro de los servos.
  core::ServoCmd c0 = core::toServo(core::Aim{true, 0.0f, 0.0f}, cal);
  TEST_ASSERT_EQUAL_FLOAT(cfg::PAN_CENTER_SERVO_DEG, c0.panServoDeg);
  TEST_ASSERT_EQUAL_FLOAT(cfg::TILT_HORIZ_SERVO_DEG, c0.tiltServoDeg);
  TEST_ASSERT_EQUAL_FLOAT(90.0f, c0.panServoDeg);
  TEST_ASSERT_EQUAL_FLOAT(90.0f, c0.tiltServoDeg);

  // Signos (se calcula con las constantes de cfg: si se invierte un signo, la prueba sigue siendo válida).
  core::ServoCmd c1 = core::toServo(core::Aim{true, -53.6f, 56.8f}, cal);
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, expectedPanServo(-53.6f, 0.0f), c1.panServoDeg);
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, expectedTiltServo(56.8f, 0.0f), c1.tiltServoDeg);
  if (cfg::PAN_SIGN == 1.0f && cfg::TILT_SIGN == 1.0f) {   // con los signos de fábrica: valores literales
    TEST_ASSERT_FLOAT_WITHIN(1e-3f, 36.4f, c1.panServoDeg);
    TEST_ASSERT_FLOAT_WITHIN(1e-3f, 146.8f, c1.tiltServoDeg);
  }

  // Trims: se suman al ángulo de servo.
  cal.panTrimDeg = 2.5f;
  cal.tiltTrimDeg = -3.0f;
  core::ServoCmd c2 = core::toServo(core::Aim{true, 0.0f, 0.0f}, cal);
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, 92.5f, c2.panServoDeg);
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, 87.0f, c2.tiltServoDeg);
  core::ServoCmd c3 = core::toServo(core::Aim{true, 20.0f, 40.0f}, cal);
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, expectedPanServo(20.0f, 2.5f), c3.panServoDeg);
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, expectedTiltServo(40.0f, -3.0f), c3.tiltServoDeg);

  // Recorte a 0..180 (con valores desmesurados, sea cual sea el signo, el resultado cae en un extremo).
  cal = core::defaultCalibration();
  core::ServoCmd hi = core::toServo(core::Aim{true, 500.0f, 500.0f}, cal);
  core::ServoCmd lo = core::toServo(core::Aim{true, -500.0f, -500.0f}, cal);
  TEST_ASSERT_TRUE(hi.panServoDeg == 0.0f || hi.panServoDeg == 180.0f);
  TEST_ASSERT_TRUE(lo.panServoDeg == 0.0f || lo.panServoDeg == 180.0f);
  TEST_ASSERT_TRUE(hi.panServoDeg != lo.panServoDeg);
  TEST_ASSERT_TRUE(hi.tiltServoDeg == 0.0f || hi.tiltServoDeg == 180.0f);
  TEST_ASSERT_TRUE(lo.tiltServoDeg == 0.0f || lo.tiltServoDeg == 180.0f);
  TEST_ASSERT_TRUE(hi.tiltServoDeg != lo.tiltServoDeg);
  // Un trim desmesurado también se recorta.
  cal.panTrimDeg = 500.0f;
  cal.tiltTrimDeg = -500.0f;
  core::ServoCmd t = core::toServo(core::Aim{true, 0.0f, 0.0f}, cal);
  TEST_ASSERT_EQUAL_FLOAT(180.0f, t.panServoDeg);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, t.tiltServoDeg);
}

static void test_approach(void) {
  core::Approach a = core::approach(100.0f, 80.0f, 2.0f);
  TEST_ASSERT_TRUE(a.needsWaypoint);
  TEST_ASSERT_EQUAL_FLOAT(78.0f, a.waypointDeg);

  a = core::approach(80.0f, 100.0f, 2.0f);
  TEST_ASSERT_FALSE(a.needsWaypoint);

  a = core::approach(90.0f, 90.0f, 2.0f);   // igual: no hay waypoint
  TEST_ASSERT_FALSE(a.needsWaypoint);

  a = core::approach(90.0f, 89.5f, 2.0f);
  TEST_ASSERT_TRUE(a.needsWaypoint);
  TEST_ASSERT_EQUAL_FLOAT(87.5f, a.waypointDeg);

  a = core::approach(50.0f, 20.0f, cfg::OVERSHOOT_DEG);
  TEST_ASSERT_TRUE(a.needsWaypoint);
  TEST_ASSERT_EQUAL_FLOAT(20.0f - cfg::OVERSHOOT_DEG, a.waypointDeg);
}

// =====================================================================================================================
// 3. Calibración: serialización
// =====================================================================================================================

// CRC16-CCITT-FALSE independiente (poly 0x1021, init 0xFFFF), solo para comprobar el blob desde fuera.
static unsigned testCrc16(const unsigned char* d, unsigned n) {
  unsigned crc = 0xFFFF;
  for (unsigned i = 0; i < n; ++i) {
    crc ^= static_cast<unsigned>(d[i]) << 8;
    for (int b = 0; b < 8; ++b) crc = (crc & 0x8000) ? (((crc << 1) ^ 0x1021) & 0xFFFF) : ((crc << 1) & 0xFFFF);
  }
  return crc;
}

static bool sameBits(float a, float b) { return memcmp(&a, &b, sizeof a) == 0; }

static bool sameCal(const core::Calibration& a, const core::Calibration& b) {
  return sameBits(a.station.xMm, b.station.xMm) && sameBits(a.station.yMm, b.station.yMm) &&
         sameBits(a.station.hMm, b.station.hMm) && sameBits(a.panTrimDeg, b.panTrimDeg) &&
         sameBits(a.tiltTrimDeg, b.tiltTrimDeg);
}

static core::Calibration makeCal(float x, float y, float h, float pt, float tt) {
  core::Calibration c;
  c.station = core::Station{x, y, h};
  c.panTrimDeg = pt;
  c.tiltTrimDeg = tt;
  return c;
}

// Vectores dorados calculados fuera del código (struct.pack('<f') + CRC16-CCITT-FALSE en Python).
static const unsigned char kGoldenDefault[25] = {0x44, 0x4C, 0x01, 0x00, 0x00, 0xC8, 0x42, 0x00, 0x00,
                                                 0x82, 0xC2, 0x00, 0x00, 0x34, 0x43, 0x00, 0x00, 0x00,
                                                 0x00, 0x00, 0x00, 0x00, 0x00, 0xDB, 0x78};
static const unsigned char kGoldenCustom[25] = {0x44, 0x4C, 0x01, 0x00, 0x00, 0xD3, 0x42, 0x00, 0x00,
                                                0x70, 0xC2, 0x00, 0x40, 0x2A, 0x43, 0x00, 0x00, 0xC0,
                                                0x3F, 0x00, 0x00, 0x00, 0xC0, 0xDE, 0x4D};   // 105.5 -60 170.25 1.5 -2

static void test_crc_helper_check_value(void) {
  const unsigned char s[] = {'1', '2', '3', '4', '5', '6', '7', '8', '9'};
  TEST_ASSERT_EQUAL_HEX16(0x29B1, testCrc16(s, 9));   // valor de control estándar de CRC-16/CCITT-FALSE
}

static void test_cal_serialize_golden(void) {
  TEST_ASSERT_EQUAL_UINT(25, core::CAL_BLOB_SIZE);
  unsigned char buf[25];
  memset(buf, 0xAA, sizeof buf);
  TEST_ASSERT_EQUAL_UINT(25, core::calSerialize(core::defaultCalibration(), buf, sizeof buf));
  TEST_ASSERT_EQUAL_HEX8_ARRAY(kGoldenDefault, buf, 25);

  TEST_ASSERT_EQUAL_UINT(25, core::calSerialize(makeCal(105.5f, -60.0f, 170.25f, 1.5f, -2.0f), buf, sizeof buf));
  TEST_ASSERT_EQUAL_HEX8_ARRAY(kGoldenCustom, buf, 25);

  // El CRC almacenado (little-endian) coincide con el calculado de forma independiente sobre los 23 bytes previos.
  const unsigned crc = testCrc16(buf, 23);
  TEST_ASSERT_EQUAL_HEX8(crc & 0xFF, buf[23]);
  TEST_ASSERT_EQUAL_HEX8((crc >> 8) & 0xFF, buf[24]);
}

static void test_cal_round_trip(void) {
  const core::Calibration cases[] = {
      core::defaultCalibration(),
      makeCal(123.456f, -78.9f, 210.5f, 1.25f, -2.5f),
      makeCal(-200.0f, -300.0f, 50.0f, -30.0f, -30.0f),
      makeCal(400.0f, 400.0f, 400.0f, 30.0f, 30.0f),
      makeCal(0.0f, -0.0f, 1e-30f, 3.14159265f, -1e10f),
  };
  for (const core::Calibration& c : cases) {
    unsigned char buf[40];
    memset(buf, 0, sizeof buf);
    TEST_ASSERT_EQUAL_UINT(25, core::calSerialize(c, buf, sizeof buf));
    TEST_ASSERT_EQUAL_HEX8('D', buf[0]);
    TEST_ASSERT_EQUAL_HEX8('L', buf[1]);
    TEST_ASSERT_EQUAL_HEX8(1, buf[2]);
    TEST_ASSERT_EQUAL_HEX8(0, buf[25]);   // no escribe más allá de CAL_BLOB_SIZE

    core::Calibration back = makeCal(7, 8, 9, 10, 11);
    TEST_ASSERT_TRUE(core::calDeserialize(buf, 25, back));
    TEST_ASSERT_TRUE_MESSAGE(sameCal(c, back), "ida y vuelta no exacta (bit a bit)");
  }
}

static void test_cal_serialize_cap_too_small(void) {
  unsigned char buf[40];
  memset(buf, 0xAA, sizeof buf);
  TEST_ASSERT_EQUAL_UINT(0, core::calSerialize(core::defaultCalibration(), buf, 24));
  TEST_ASSERT_EQUAL_UINT(0, core::calSerialize(core::defaultCalibration(), buf, 0));
  for (unsigned i = 0; i < sizeof buf; ++i) TEST_ASSERT_EQUAL_HEX8(0xAA, buf[i]);   // sin escribir nada
  TEST_ASSERT_EQUAL_UINT(0, core::calSerialize(core::defaultCalibration(), nullptr, 100));
  TEST_ASSERT_EQUAL_UINT(25, core::calSerialize(core::defaultCalibration(), buf, 25));   // justo
}

static void test_cal_deserialize_rejects_corruption(void) {
  unsigned char good[25];
  TEST_ASSERT_EQUAL_UINT(25, core::calSerialize(makeCal(123.456f, -78.9f, 210.5f, 1.25f, -2.5f), good, sizeof good));
  const core::Calibration sentinel = makeCal(7, 8, 9, 10, 11);

  // Un bit cambiado en cualquiera de los 25 bytes (magia, versión, datos o CRC) invalida el blob.
  for (unsigned i = 0; i < 25; ++i) {
    for (unsigned bit = 0; bit < 8; bit += 7) {   // bits 0 y 7
      unsigned char bad[25];
      memcpy(bad, good, sizeof bad);
      bad[i] = static_cast<unsigned char>(bad[i] ^ (1u << bit));
      core::Calibration out = sentinel;
      char msg[48];
      snprintf(msg, sizeof msg, "byte %u bit %u", i, bit);
      TEST_ASSERT_FALSE_MESSAGE(core::calDeserialize(bad, 25, out), msg);
      TEST_ASSERT_TRUE_MESSAGE(sameCal(sentinel, out), "out no debe modificarse al fallar");
    }
  }

  // Magia o versión erróneas CON el CRC recalculado: igualmente inválido.
  unsigned char bad[25];
  core::Calibration out = sentinel;

  memcpy(bad, good, sizeof bad);
  bad[0] = 'X';
  { const unsigned c = testCrc16(bad, 23); bad[23] = c & 0xFF; bad[24] = (c >> 8) & 0xFF; }
  TEST_ASSERT_FALSE(core::calDeserialize(bad, 25, out));

  memcpy(bad, good, sizeof bad);
  bad[1] = 'X';
  { const unsigned c = testCrc16(bad, 23); bad[23] = c & 0xFF; bad[24] = (c >> 8) & 0xFF; }
  TEST_ASSERT_FALSE(core::calDeserialize(bad, 25, out));

  memcpy(bad, good, sizeof bad);
  bad[2] = 2;   // versión futura
  { const unsigned c = testCrc16(bad, 23); bad[23] = c & 0xFF; bad[24] = (c >> 8) & 0xFF; }
  TEST_ASSERT_FALSE(core::calDeserialize(bad, 25, out));

  memcpy(bad, good, sizeof bad);
  bad[2] = 0;
  { const unsigned c = testCrc16(bad, 23); bad[23] = c & 0xFF; bad[24] = (c >> 8) & 0xFF; }
  TEST_ASSERT_FALSE(core::calDeserialize(bad, 25, out));

  TEST_ASSERT_TRUE(sameCal(sentinel, out));

  // Longitud errónea (aunque el contenido sea válido).
  unsigned char big[40];
  memset(big, 0, sizeof big);
  memcpy(big, good, 25);
  TEST_ASSERT_FALSE(core::calDeserialize(big, 24, out));
  TEST_ASSERT_FALSE(core::calDeserialize(big, 26, out));
  TEST_ASSERT_FALSE(core::calDeserialize(big, 0, out));
  TEST_ASSERT_FALSE(core::calDeserialize(big, 50, out));
  TEST_ASSERT_FALSE(core::calDeserialize(nullptr, 25, out));
  TEST_ASSERT_TRUE(sameCal(sentinel, out));

  // Y el blob bueno sigue siendo válido.
  TEST_ASSERT_TRUE(core::calDeserialize(good, 25, out));
  expectCal(out, 123.456f, -78.9f, 210.5f, 1.25f, -2.5f);
}

// =====================================================================================================================
// 4. Controlador con HAL falsos
// =====================================================================================================================

static void test_begin_laser_off_first_and_servos_free(void) {
  Rig r;
  r.log.laserOn = true;   // láser "sucio" antes de begin()
  r.store.hasData = true;
  r.store.data = makeCal(105.0f, -60.0f, 170.0f, 1.5f, -2.0f);
  r.ctrl.begin();

  TEST_ASSERT_TRUE(r.log.events.size() >= 1);
  TEST_ASSERT_EQUAL_INT_MESSAGE(static_cast<int>(Ev::LaserSet), static_cast<int>(r.log.events[0].kind),
                                "lo primero de begin() debe ser apagar el laser");
  TEST_ASSERT_FALSE(r.log.events[0].on);
  TEST_ASSERT_FALSE(r.log.laserOn);
  TEST_ASSERT_FALSE(r.laser.isOn());

  // Los servos no se activan ni se escriben.
  TEST_ASSERT_EQUAL_INT(0, r.pan.attaches);
  TEST_ASSERT_EQUAL_INT(0, r.tilt.attaches);
  TEST_ASSERT_EQUAL_INT(0, countKind(r, Ev::ServoAttach));
  TEST_ASSERT_EQUAL_INT(0, countKind(r, Ev::ServoWrite));
  TEST_ASSERT_FALSE(r.pan.attached);
  TEST_ASSERT_FALSE(r.tilt.attached);

  // Carga la calibración del almacén; no queda ocupado.
  expectCal(r.ctrl.calibration(), 105.0f, -60.0f, 170.0f, 1.5f, -2.0f);
  TEST_ASSERT_FALSE(r.ctrl.busy());
}

static void test_begin_defaults_when_store_empty_or_invalid(void) {
  {
    Rig r;   // sin datos guardados
    r.ctrl.begin();
    expectDefaultCal(r.ctrl.calibration());
    TEST_ASSERT_EQUAL_INT(1, r.store.loads);
  }
  {
    Rig r;   // datos "válidos" para el almacén pero fuera de los rangos de CAL SET (h = 10)
    r.store.hasData = true;
    r.store.data = makeCal(100.0f, -65.0f, 10.0f, 0.0f, 0.0f);
    r.ctrl.begin();
    expectDefaultCal(r.ctrl.calibration());
  }
}

static void test_begin_again_frees_servos(void) {
  Rig r;
  r.ctrl.begin();
  r.send("(11,11)");
  TEST_ASSERT_TRUE(r.pan.attached);
  const size_t m = mark(r);
  r.ctrl.begin();
  const std::vector<std::string> d = describe(r, m);
  TEST_ASSERT_TRUE(d.size() >= 1);
  TEST_ASSERT_EQUAL_STRING("LASER 0", d[0].c_str());   // el láser, siempre primero
  TEST_ASSERT_FALSE(r.pan.attached);
  TEST_ASSERT_FALSE(r.tilt.attached);
  EXPECT_TOKENS(std::vector<std::string>({"LASER 0", "STORE LOAD", "DETACH pan", "DETACH tilt"}), d);
  TEST_ASSERT_EQUAL_INT(2, countKind(r, Ev::ServoAttach));   // los dos del primer disparo; begin() no activa nada
}

static void test_fire_exact_sequence(void) {
  Rig r;
  r.ctrl.begin();
  const size_t m = mark(r);
  const std::vector<std::string> reply = r.send("(11,11)");
  EXPECT_REPLIES(reply, "OK (11,11)");

  // Celda (11,11): pan servo 91.68, tilt servo 136.62. Ambos suben desde 90, así que no hay waypoint.
  const std::vector<std::string> expected = cat(
      {"LASER 0", "ATTACH pan", "ATTACH tilt", "W pan 90.00", "W tilt 90.00",
       "MOVE pan up n=1 end=91.68", "MOVE tilt up n=24 end=136.62"},
      shotTail(11, 11));
  EXPECT_TOKENS(expected, describe(r, m));
  checkSafety(r);
  TEST_ASSERT_FALSE(r.ctrl.busy());
  // Los servos quedan activos (reteniendo).
  TEST_ASSERT_TRUE(r.pan.attached);
  TEST_ASSERT_TRUE(r.tilt.attached);
}

static void test_fire_waypoint_when_descending(void) {
  Rig r;
  r.ctrl.begin();
  r.send("(11,11)");

  // (11,11) -> (1,1): el pan baja de 91.68 a 36.38 (waypoint 34.38, luego sube 2°); el tilt sube de 136.62 a 146.75.
  size_t m = mark(r);
  std::vector<std::string> reply = r.send("(1,1)");
  EXPECT_REPLIES(reply, "OK (1,1)");
  EXPECT_TOKENS(cat({"LASER 0", "MOVE pan down n=29 end=34.38", "MOVE pan up n=1 end=36.38",
                     "MOVE tilt up n=6 end=146.75"},
                    shotTail(1, 1)),
                describe(r, m));

  // (1,1) -> (20,20): el pan sube hasta 110.07 (sin waypoint); el tilt baja de 146.75 a 123.03 (waypoint 121.03).
  m = mark(r);
  reply = r.send("(20,20)");
  EXPECT_REPLIES(reply, "OK (20,20)");
  EXPECT_TOKENS(cat({"LASER 0", "MOVE pan up n=37 end=110.07", "MOVE tilt down n=13 end=121.03",
                     "MOVE tilt up n=1 end=123.03"},
                    shotTail(20, 20)),
                describe(r, m));

  // Repetir la misma celda: ya está allí, no hay movimiento ni waypoint.
  m = mark(r);
  reply = r.send("(20,20)");
  EXPECT_REPLIES(reply, "OK (20,20)");
  EXPECT_TOKENS(cat({"LASER 0"}, shotTail(20, 20)), describe(r, m));

  checkSafety(r);
}

static void test_fire_laser_timing(void) {
  Rig r;
  r.ctrl.begin();
  r.send("(7,13)");
  uint32_t lastWriteT = 0;
  uint32_t onT = 0, offT = 0;
  bool haveOn = false;
  for (const Event& e : r.log.events) {
    if (e.kind == Ev::ServoWrite) lastWriteT = e.t;
    if (e.kind == Ev::LaserSet && e.on) { onT = e.t; haveOn = true; }
    if (e.kind == Ev::LaserSet && !e.on && haveOn) offT = e.t;
  }
  TEST_ASSERT_TRUE(haveOn);
  // Tras el último movimiento: al menos SETTLE_MS antes de encender.
  TEST_ASSERT_TRUE(onT >= lastWriteT + cfg::SETTLE_MS);
  // Permanencia: al menos LASER_ON_MS (el pitido, que bloquea BEEP_MS, ocurre con el láser ya encendido).
  TEST_ASSERT_TRUE(offT - onT >= cfg::LASER_ON_MS);
  TEST_ASSERT_TRUE(offT - onT <= cfg::LASER_ON_MS + cfg::BEEP_MS);
}

// Xorshift determinista para recorrer las 400 celdas en un orden "aleatorio" (sube y baja ángulos).
static unsigned nextRand(unsigned& s) {
  s ^= s << 13;
  s ^= s >> 17;
  s ^= s << 5;
  return s;
}

static void test_fire_all_cells_safety_invariants(void) {
  Rig r;
  r.ctrl.begin();

  int order[400];
  for (int i = 0; i < 400; ++i) order[i] = i;
  unsigned seed = 2463534242u;
  for (int i = 399; i > 0; --i) {
    const int j = static_cast<int>(nextRand(seed) % static_cast<unsigned>(i + 1));
    const int t = order[i];
    order[i] = order[j];
    order[j] = t;
  }

  for (int k = 0; k < 400; ++k) {
    const int x = order[k] % 20 + 1;
    const int y = order[k] / 20 + 1;
    char line[32];
    snprintf(line, sizeof line, "(%d,%d)", x, y);
    const std::vector<std::string> reply = r.send(line);
    char want[48];
    snprintf(want, sizeof want, "OK (%d,%d)", x, y);
    TEST_ASSERT_EQUAL_INT_MESSAGE(1, static_cast<int>(reply.size()), line);
    TEST_ASSERT_EQUAL_STRING_MESSAGE(want, reply[0].c_str(), line);
  }

  checkSafety(r);
  TEST_ASSERT_EQUAL_INT(400, countLaserOn(r));
  TEST_ASSERT_EQUAL_INT(400, countKind(r, Ev::Beep));

  // Aproximación: antes de cada encendido del láser, el último paso de cada servo fue hacia ángulos MAYORES.
  float lastW[2] = {NAN, NAN};
  float lastDelta[2] = {0.0f, 0.0f};
  for (size_t i = 0; i < r.log.events.size(); ++i) {
    const Event& e = r.log.events[i];
    if (e.kind == Ev::ServoWrite) {
      if (!std::isnan(lastW[e.servo])) lastDelta[e.servo] = e.deg - lastW[e.servo];
      lastW[e.servo] = e.deg;
    } else if (e.kind == Ev::LaserSet && e.on) {
      TEST_ASSERT_TRUE_MESSAGE(lastDelta[0] >= 0.0f && lastDelta[1] >= 0.0f, "llegada al destino desde ángulos menores");
    }
  }
}

static void test_syntax_errors_touch_no_hardware(void) {
  Rig r;
  r.ctrl.begin();
  const size_t m = mark(r);
  EXPECT_REPLIES(r.send(""), "ERR EMPTY");
  EXPECT_REPLIES(r.send(std::string(65, 'A')), "ERR TOOLONG");
  EXPECT_REPLIES(r.send("(a,b)"), "ERR FORMAT");
  EXPECT_REPLIES(r.send("12,7"), "ERR FORMAT");
  EXPECT_REPLIES(r.send("(0,5)"), "ERR RANGE");
  EXPECT_REPLIES(r.send("(21,1)"), "ERR RANGE");
  EXPECT_REPLIES(r.send("(1,21)"), "ERR RANGE");
  EXPECT_REPLIES(r.send("HOLA"), "ERR UNKNOWN");
  EXPECT_REPLIES(r.send("CAL SET 1 2"), "ERR FORMAT");

  // Solo respuestas: ni láser, ni servos, ni esperas.
  for (size_t i = m; i < r.log.events.size(); ++i) {
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Ev::Reply), static_cast<int>(r.log.events[i].kind));
  }
  TEST_ASSERT_FALSE(r.ctrl.busy());
}

static void test_err_limit(void) {
  Rig r;
  r.ctrl.begin();
  // Con la estación 300 mm a la derecha, la celda (1,1) queda a -80° de pan: fuera del límite de 57°.
  EXPECT_REPLIES(r.send("CAL SET 400 -65 180 0 0"), "OK CAL");
  const size_t m = mark(r);
  EXPECT_REPLIES(r.send("(1,1)"), "ERR LIMIT");
  EXPECT_TOKENS(std::vector<std::string>({"REPLY ERR LIMIT"}), describe(r, m));   // nada de hardware
  TEST_ASSERT_EQUAL_INT(0, r.pan.attaches);
  TEST_ASSERT_FALSE(r.ctrl.busy());
  // Con esa estación tampoco cabe (11,11) (pan -60°): ERR LIMIT; tras CAL RESET vuelve a funcionar.
  EXPECT_REPLIES(r.send("(11,11)"), "ERR LIMIT");
  EXPECT_REPLIES(r.send("CAL RESET"), "OK RESET");
  EXPECT_REPLIES(r.send("(11,11)"), "OK (11,11)");
  checkSafety(r);
}

static void test_busy_rejects_other_commands(void) {
  Rig r;
  r.ctrl.begin();
  std::vector<std::string> nested;
  bool busyDuring = false;
  bool fired = false;
  r.log.hook = [&](const Event& e) {
    if (e.kind == Ev::Delay && e.ms == cfg::SETTLE_MS && !fired) {
      fired = true;
      busyDuring = r.ctrl.busy();
      nested.push_back(join(r.send("(5,5)")));
      nested.push_back(join(r.send("PING")));
      nested.push_back(join(r.send("TEST")));
      nested.push_back(join(r.send("CAL SHOW")));
      nested.push_back(join(r.send("CAL SET 100 -65 180 0 0")));
      nested.push_back(join(r.send("CAL SAVE")));
      nested.push_back(join(r.send("MARK HIT")));
      nested.push_back(join(r.send("HOLA")));   // los errores de sintaxis se responden antes que BUSY
    }
  };
  const std::vector<std::string> reply = r.send("(11,11)");
  r.log.hook = nullptr;

  TEST_ASSERT_TRUE(fired);
  TEST_ASSERT_TRUE(busyDuring);
  EXPECT_REPLIES(reply, "OK (11,11)");
  EXPECT_REPLIES(nested, "ERR BUSY", "ERR BUSY", "ERR BUSY", "ERR BUSY", "ERR BUSY", "ERR BUSY", "ERR BUSY", "ERR UNKNOWN");
  TEST_ASSERT_FALSE(r.ctrl.busy());
  // Las órdenes rechazadas no tocaron el hardware: un solo disparo, sin LED ni almacén.
  TEST_ASSERT_EQUAL_INT(1, countLaserOn(r));
  TEST_ASSERT_EQUAL_INT(1, countKind(r, Ev::Beep));
  TEST_ASSERT_EQUAL_INT(0, countKind(r, Ev::LedSet));
  TEST_ASSERT_EQUAL_INT(0, countKind(r, Ev::StoreSave));
  TEST_ASSERT_EQUAL_INT(0, r.store.saves);
  checkSafety(r);
}

static void test_stop_when_idle_does_not_block_next_shot(void) {
  Rig r;
  r.ctrl.begin();
  EXPECT_REPLIES(r.send("STOP"), "OK STOP");
  TEST_ASSERT_FALSE(r.log.laserOn);
  TEST_ASSERT_FALSE(r.ctrl.busy());
  EXPECT_REPLIES(r.send("stop"), "OK STOP");
  EXPECT_REPLIES(r.send("(11,11)"), "OK (11,11)");   // un STOP sin disparo en curso no aborta el siguiente
  EXPECT_REPLIES(r.send("(3,3)"), "OK (3,3)");
  checkSafety(r);
}

static void test_stop_during_move(void) {
  Rig r;
  r.ctrl.begin();
  std::vector<std::string> nested;
  int writes = 0;
  size_t stopAt = 0;
  r.log.hook = [&](const Event& e) {
    if (e.kind == Ev::ServoWrite && ++writes == 5) {   // 2 escrituras de retención + 3.er paso de la rampa del pan
      nested = r.send("STOP");
      stopAt = r.log.events.size();
    }
  };
  const std::vector<std::string> reply = r.send("(20,20)");
  r.log.hook = nullptr;

  EXPECT_REPLIES(nested, "OK STOP");
  EXPECT_REPLIES(reply, "ERR STOP");
  TEST_ASSERT_TRUE(stopAt > 0);
  TEST_ASSERT_EQUAL_INT_MESSAGE(0, countLaserOn(r), "no debe encenderse el laser");
  TEST_ASSERT_EQUAL_INT(0, countKind(r, Ev::Beep));
  for (size_t i = stopAt; i < r.log.events.size(); ++i) {
    TEST_ASSERT_FALSE_MESSAGE(r.log.events[i].kind == Ev::ServoWrite, "no debe haber escrituras de servo tras el STOP");
  }
  TEST_ASSERT_FALSE(r.ctrl.busy());
  checkSafety(r);

  // Después se puede volver a disparar desde la posición en que quedó.
  EXPECT_REPLIES(r.send("(11,11)"), "OK (11,11)");
  checkSafety(r);
}

static void test_stop_during_settle_never_turns_laser_on(void) {
  Rig r;
  r.ctrl.begin();
  std::vector<std::string> nested;
  r.log.hook = [&](const Event& e) {
    if (e.kind == Ev::Delay && e.ms == cfg::SETTLE_MS) nested = r.send("STOP");
  };
  const std::vector<std::string> reply = r.send("(11,11)");
  r.log.hook = nullptr;

  EXPECT_REPLIES(nested, "OK STOP");
  EXPECT_REPLIES(reply, "ERR STOP");
  TEST_ASSERT_EQUAL_INT(0, countLaserOn(r));
  TEST_ASSERT_EQUAL_INT(0, countKind(r, Ev::Beep));
  checkSafety(r);
}

static void test_stop_right_after_laser_on_turns_it_off(void) {
  // Carrera: el STOP llega justo entre la comprobación del interlock y el encendido del láser.
  Rig r;
  r.ctrl.begin();
  bool fired = false;
  r.log.hook = [&](const Event& e) {
    if (e.kind == Ev::LaserSet && e.on && !fired) {
      fired = true;
      r.ctrl.requestStop();
    }
  };
  const std::vector<std::string> reply = r.send("(11,11)");
  r.log.hook = nullptr;

  TEST_ASSERT_TRUE(fired);
  EXPECT_REPLIES(reply, "ERR STOP");
  TEST_ASSERT_EQUAL_INT(0, countKind(r, Ev::Beep));   // ni pitido ni permanencia
  TEST_ASSERT_FALSE(r.log.laserOn);
  checkSafety(r);
}

static void test_stop_during_beep_skips_dwell(void) {
  Rig r;
  r.ctrl.begin();
  r.log.hook = [&](const Event& e) {
    if (e.kind == Ev::Beep) r.ctrl.requestStop();
  };
  const std::vector<std::string> reply = r.send("(11,11)");
  r.log.hook = nullptr;

  EXPECT_REPLIES(reply, "ERR STOP");
  for (const Event& e : r.log.events) {
    TEST_ASSERT_FALSE_MESSAGE(e.kind == Ev::Delay && e.ms == cfg::LASER_ON_MS, "no debe esperar la permanencia tras un STOP");
  }
  TEST_ASSERT_FALSE(r.log.laserOn);
  checkSafety(r);
}

static void test_stop_during_dwell_turns_laser_off_immediately(void) {
  Rig r;
  r.ctrl.begin();
  std::vector<std::string> nested;
  bool offRightAway = false;
  bool onBefore = false;
  r.log.hook = [&](const Event& e) {
    // La espera de permanencia es el Delay(LASER_ON_MS) con el láser encendido.
    if (e.kind == Ev::Delay && e.ms == cfg::LASER_ON_MS && e.laserOn) {
      onBefore = r.log.laserOn;
      nested = r.send("STOP");
      offRightAway = !r.log.laserOn;   // el láser se apaga DENTRO de la orden STOP, sin esperar al fin del disparo
    }
  };
  const std::vector<std::string> reply = r.send("(11,11)");
  r.log.hook = nullptr;

  TEST_ASSERT_TRUE(onBefore);
  TEST_ASSERT_TRUE(offRightAway);
  EXPECT_REPLIES(nested, "OK STOP");
  EXPECT_REPLIES(reply, "ERR STOP");
  TEST_ASSERT_EQUAL_INT(1, countLaserOn(r));
  TEST_ASSERT_FALSE(r.log.laserOn);
  checkSafety(r);
}

static void test_test_routine(void) {
  Rig r;
  r.ctrl.begin();
  const size_t m = mark(r);
  const std::vector<std::string> reply = r.send("TEST");

  std::vector<std::string> expected = {"TEST START"};
  for (const auto& c : cfg::TEST_CELLS) expected.push_back(core::fireOkText(c[0], c[1]));
  expected.push_back("TEST DONE");
  TEST_ASSERT_EQUAL_INT(7, static_cast<int>(expected.size()));
  EXPECT_TOKENS(expected, reply);

  // Orden entre respuestas y hardware: "TEST START" antes de todo; cada "OK (x,y)" tras la permanencia del láser y
  // antes de la pausa entre posiciones; "TEST DONE" al final, tras la última pausa.
  std::vector<std::string> outline, wanted;
  for (const std::string& t : describe(r, m)) {
    if (t.compare(0, 5, "REPLY") == 0 || t == "LASER 1" || t == "DELAY " + num(cfg::LASER_ON_MS) ||
        t == "DELAY " + num(cfg::TEST_GAP_MS)) {
      outline.push_back(t);
    }
  }
  wanted.push_back("REPLY TEST START");
  for (const auto& c : cfg::TEST_CELLS) {
    wanted.push_back("LASER 1");
    wanted.push_back("DELAY " + num(cfg::LASER_ON_MS));
    wanted.push_back("REPLY " + core::fireOkText(c[0], c[1]));
    wanted.push_back("DELAY " + num(cfg::TEST_GAP_MS));
  }
  wanted.push_back("REPLY TEST DONE");
  EXPECT_TOKENS(wanted, outline);

  TEST_ASSERT_EQUAL_INT(5, countLaserOn(r));
  TEST_ASSERT_EQUAL_INT(5, countKind(r, Ev::Beep));
  checkSafety(r);
  TEST_ASSERT_FALSE(r.ctrl.busy());
}

static void test_test_aborts_on_limit(void) {
  Rig r;
  r.ctrl.begin();
  // Con la estación en x=85, (1,1) queda a -48.8° pero (20,1) a +57.5° (límite 57°).
  EXPECT_REPLIES(r.send("CAL SET 85 -65 180 0 0"), "OK CAL");
  EXPECT_REPLIES(r.send("TEST"), "TEST START", "OK (1,1)", "TEST ABORT", "ERR LIMIT");
  TEST_ASSERT_EQUAL_INT(1, countLaserOn(r));
  TEST_ASSERT_FALSE(r.ctrl.busy());
  checkSafety(r);

  // Y si falla la primera posición: sin ningún disparo.
  Rig r2;
  r2.ctrl.begin();
  EXPECT_REPLIES(r2.send("CAL SET 400 -65 180 0 0"), "OK CAL");
  EXPECT_REPLIES(r2.send("TEST"), "TEST START", "TEST ABORT", "ERR LIMIT");
  TEST_ASSERT_EQUAL_INT(0, countLaserOn(r2));
  TEST_ASSERT_EQUAL_INT(0, r2.pan.attaches);
}

static void test_test_aborts_on_stop(void) {
  {   // STOP durante el 2.º disparo
    Rig r;
    r.ctrl.begin();
    int settles = 0;
    r.log.hook = [&](const Event& e) {
      if (e.kind == Ev::Delay && e.ms == cfg::SETTLE_MS && ++settles == 2) r.ctrl.requestStop();
    };
    EXPECT_REPLIES(r.send("TEST"), "TEST START", "OK (1,1)", "TEST ABORT", "ERR STOP");
    r.log.hook = nullptr;
    TEST_ASSERT_EQUAL_INT(1, countLaserOn(r));
    checkSafety(r);
  }
  {   // STOP durante la pausa entre posiciones
    Rig r;
    r.ctrl.begin();
    bool fired = false;
    r.log.hook = [&](const Event& e) {
      const size_t n = r.log.events.size();
      if (!fired && e.kind == Ev::Delay && n >= 2 && r.log.events[n - 2].kind == Ev::Reply) {   // Delay justo tras una respuesta
        fired = true;
        r.ctrl.requestStop();
      }
    };
    EXPECT_REPLIES(r.send("TEST"), "TEST START", "OK (1,1)", "TEST ABORT", "ERR STOP");
    r.log.hook = nullptr;
    TEST_ASSERT_TRUE(fired);
    TEST_ASSERT_EQUAL_INT(1, countLaserOn(r));
    checkSafety(r);
  }
}

static void test_ping(void) {
  Rig r;
  r.ctrl.begin();
  const std::string expected = std::string("PONG ") + DEVICE_NAME + " " + FW_VERSION;
  EXPECT_REPLIES(r.send("PING"), expected);
  EXPECT_REPLIES(r.send("ping\r\n"), expected);
  TEST_ASSERT_EQUAL_STRING("PONG DUELO-A 0.1.0", expected.c_str());   // valores por defecto de config.h
}

static void test_cal_show_and_set(void) {
  Rig r;
  r.ctrl.begin();
  EXPECT_REPLIES(r.send("CAL SHOW"), "CAL 100.00 -65.00 180.00 0.00 0.00");

  EXPECT_REPLIES(r.send("CAL SET 105.5 -60 170.25 1.5 -2"), "OK CAL");
  expectCal(r.ctrl.calibration(), 105.5f, -60.0f, 170.25f, 1.5f, -2.0f);
  EXPECT_REPLIES(r.send("cal show"), "CAL 105.50 -60.00 170.25 1.50 -2.00");

  // Límites aceptados (inclusivos).
  EXPECT_REPLIES(r.send("CAL SET -200 -300 50 -10 -10"), "OK CAL");
  EXPECT_REPLIES(r.send("CAL SHOW"), "CAL -200.00 -300.00 50.00 -10.00 -10.00");
  EXPECT_REPLIES(r.send("CAL SET 400 400 400 10 10"), "OK CAL");
  EXPECT_REPLIES(r.send("CAL SHOW"), "CAL 400.00 400.00 400.00 10.00 10.00");
  EXPECT_REPLIES(r.send("CAL SET 100 -65 180 -0.001 0"), "OK CAL");
  EXPECT_REPLIES(r.send("CAL SHOW"), "CAL 100.00 -65.00 180.00 0.00 0.00");   // sin "-0.00"

  // Servos y láser intactos: CAL no mueve nada.
  TEST_ASSERT_EQUAL_INT(0, countKind(r, Ev::ServoWrite));
  TEST_ASSERT_EQUAL_INT(0, countLaserOn(r));
}

static void test_cal_set_range_and_format_errors(void) {
  const char* bad[] = {
      "CAL SET 100 -65 49.9 0 0",   "CAL SET 100 -65 400.1 0 0",  "CAL SET -200.1 -65 180 0 0", "CAL SET 400.1 -65 180 0 0",
      "CAL SET 100 -300.1 180 0 0", "CAL SET 100 400.1 180 0 0",  "CAL SET 100 -65 180 10.1 0", "CAL SET 100 -65 180 -10.1 0",
      "CAL SET 100 -65 180 0 10.1", "CAL SET 100 -65 180 0 -10.1", "CAL SET 0 0 0 0 0",         "CAL SET 100 -65 1e9 0 0",
  };
  Rig r;
  r.ctrl.begin();
  EXPECT_REPLIES(r.send("CAL SET 101 -64 181 1 -1"), "OK CAL");   // estado de partida conocido
  for (const char* line : bad) {
    const std::vector<std::string> reply = r.send(line);
    if (std::string(line).find("1e9") != std::string::npos) {   // notación científica: ni se acepta como número
      TEST_ASSERT_EQUAL_STRING_MESSAGE("ERR FORMAT", join(reply).c_str(), line);
    } else {
      TEST_ASSERT_EQUAL_STRING_MESSAGE("ERR RANGE", join(reply).c_str(), line);
    }
    expectCal(r.ctrl.calibration(), 101.0f, -64.0f, 181.0f, 1.0f, -1.0f);   // sin cambios
  }
  EXPECT_REPLIES(r.send("CAL SET 1 2"), "ERR FORMAT");
  EXPECT_REPLIES(r.send("CAL SET a b c d e"), "ERR FORMAT");
  expectCal(r.ctrl.calibration(), 101.0f, -64.0f, 181.0f, 1.0f, -1.0f);
}

static void test_cal_save_reset_and_persistence(void) {
  Rig r;
  r.ctrl.begin();
  EXPECT_REPLIES(r.send("CAL SET 105.5 -60 170.25 1.5 -2"), "OK CAL");

  EXPECT_REPLIES(r.send("CAL SAVE"), "OK SAVE");
  TEST_ASSERT_EQUAL_INT(1, r.store.saves);
  TEST_ASSERT_TRUE(r.store.hasData);
  expectCal(r.store.data, 105.5f, -60.0f, 170.25f, 1.5f, -2.0f);

  // Un cambio sin guardar se pierde al reiniciar: begin() recarga lo guardado.
  EXPECT_REPLIES(r.send("CAL SET 110 -62 175 0 0"), "OK CAL");
  expectCal(r.ctrl.calibration(), 110.0f, -62.0f, 175.0f, 0.0f, 0.0f);
  r.ctrl.begin();
  expectCal(r.ctrl.calibration(), 105.5f, -60.0f, 170.25f, 1.5f, -2.0f);

  // Fallo del almacén.
  r.store.saveOk = false;
  EXPECT_REPLIES(r.send("CAL SAVE"), "ERR STORE");
  TEST_ASSERT_EQUAL_INT(2, r.store.saves);
  expectCal(r.ctrl.calibration(), 105.5f, -60.0f, 170.25f, 1.5f, -2.0f);   // la calibración en RAM no se pierde
  r.store.saveOk = true;

  // CAL RESET: valores por defecto y borrado del almacén.
  EXPECT_REPLIES(r.send("CAL RESET"), "OK RESET");
  expectDefaultCal(r.ctrl.calibration());
  TEST_ASSERT_EQUAL_INT(1, r.store.erases);
  TEST_ASSERT_FALSE(r.store.hasData);
  EXPECT_REPLIES(r.send("CAL SHOW"), "CAL 100.00 -65.00 180.00 0.00 0.00");
  r.ctrl.begin();
  expectDefaultCal(r.ctrl.calibration());
}

static void test_mark_hit_and_miss(void) {
  Rig r;
  r.ctrl.begin();

  size_t m = mark(r);
  EXPECT_REPLIES(r.send("MARK HIT"), "OK MARK");
  EXPECT_TOKENS(std::vector<std::string>({"LED 1", "DELAY " + num(cfg::LED_HIT_MS), "LED 0", "REPLY OK MARK"}),
                describe(r, m));
  uint32_t onT = 0, offT = 0;
  for (const Event& e : r.log.events) {
    if (e.kind == Ev::LedSet && e.on) onT = e.t;
    if (e.kind == Ev::LedSet && !e.on) offT = e.t;
  }
  TEST_ASSERT_EQUAL_UINT32(cfg::LED_HIT_MS, offT - onT);   // 2000 ms encendido
  TEST_ASSERT_FALSE(r.log.ledOn);

  m = mark(r);
  EXPECT_REPLIES(r.send("mark miss"), "OK MARK");
  EXPECT_TOKENS(std::vector<std::string>({"REPLY OK MARK"}), describe(r, m));   // sin LED ni esperas
  TEST_ASSERT_FALSE(r.ctrl.busy());
}

static void test_null_reply_is_safe(void) {
  Rig r;
  r.ctrl.begin();
  r.ctrl.handleLine("PING", nullptr);
  r.ctrl.handleLine("STOP", nullptr);
  r.ctrl.handleLine("(11,11)", nullptr);
  r.ctrl.handleLine("???", nullptr);
  TEST_ASSERT_FALSE(r.ctrl.busy());
  checkSafety(r);
}

// =====================================================================================================================

int main() {
  UNITY_BEGIN();

  // 1. Analizador
  RUN_TEST(test_parse_fire_valid);
  RUN_TEST(test_parse_keywords);
  RUN_TEST(test_parse_cal_set);
  RUN_TEST(test_parse_range_errors);
  RUN_TEST(test_parse_bad_format);
  RUN_TEST(test_parse_empty);
  RUN_TEST(test_parse_too_long);
  RUN_TEST(test_parse_unknown);
  RUN_TEST(test_error_and_ok_texts);

  // 2. Geometría
  RUN_TEST(test_cell_in_range);
  RUN_TEST(test_default_station_and_calibration);
  RUN_TEST(test_aim_known_vectors);
  RUN_TEST(test_aim_all_400_cells_ok);
  RUN_TEST(test_aim_cell_out_of_range_is_not_ok);
  RUN_TEST(test_aim_at_mm);
  RUN_TEST(test_aim_uses_station);
  RUN_TEST(test_to_servo);
  RUN_TEST(test_approach);

  // 3. Calibración
  RUN_TEST(test_crc_helper_check_value);
  RUN_TEST(test_cal_serialize_golden);
  RUN_TEST(test_cal_round_trip);
  RUN_TEST(test_cal_serialize_cap_too_small);
  RUN_TEST(test_cal_deserialize_rejects_corruption);

  // 4. Controlador
  RUN_TEST(test_begin_laser_off_first_and_servos_free);
  RUN_TEST(test_begin_defaults_when_store_empty_or_invalid);
  RUN_TEST(test_begin_again_frees_servos);
  RUN_TEST(test_fire_exact_sequence);
  RUN_TEST(test_fire_waypoint_when_descending);
  RUN_TEST(test_fire_laser_timing);
  RUN_TEST(test_fire_all_cells_safety_invariants);
  RUN_TEST(test_syntax_errors_touch_no_hardware);
  RUN_TEST(test_err_limit);
  RUN_TEST(test_busy_rejects_other_commands);
  RUN_TEST(test_stop_when_idle_does_not_block_next_shot);
  RUN_TEST(test_stop_during_move);
  RUN_TEST(test_stop_during_settle_never_turns_laser_on);
  RUN_TEST(test_stop_right_after_laser_on_turns_it_off);
  RUN_TEST(test_stop_during_beep_skips_dwell);
  RUN_TEST(test_stop_during_dwell_turns_laser_off_immediately);
  RUN_TEST(test_test_routine);
  RUN_TEST(test_test_aborts_on_limit);
  RUN_TEST(test_test_aborts_on_stop);
  RUN_TEST(test_ping);
  RUN_TEST(test_cal_show_and_set);
  RUN_TEST(test_cal_set_range_and_format_errors);
  RUN_TEST(test_cal_save_reset_and_persistence);
  RUN_TEST(test_mark_hit_and_miss);
  RUN_TEST(test_null_reply_is_safe);

  return UNITY_END();
}
