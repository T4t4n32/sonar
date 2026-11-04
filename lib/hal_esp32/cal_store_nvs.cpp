// hal::CalStore sobre NVS (Preferences): namespace "duelo", clave "cal", blob = core::calSerialize.
#include <Preferences.h>
#include "geometry.h"
#include "hal_esp32.h"

namespace {
constexpr const char* kNamespace = "duelo";
constexpr const char* kKey = "cal";
}  // namespace

namespace hal_esp32 {

bool NvsCalStore::load(core::Calibration& out) {
  Preferences prefs;
  if (!prefs.begin(kNamespace, /*readOnly=*/true)) return false;   // el namespace aún no existe: no hay datos
  unsigned char blob[core::CAL_BLOB_SIZE];
  bool ok = false;
  if (prefs.getBytesLength(kKey) == core::CAL_BLOB_SIZE &&
      prefs.getBytes(kKey, blob, sizeof(blob)) == core::CAL_BLOB_SIZE) {
    ok = core::calDeserialize(blob, core::CAL_BLOB_SIZE, out);     // verifica magia, versión y CRC
  }
  prefs.end();
  return ok;
}

bool NvsCalStore::save(const core::Calibration& c) {
  unsigned char blob[core::CAL_BLOB_SIZE];
  if (core::calSerialize(c, blob, sizeof(blob)) != core::CAL_BLOB_SIZE) return false;
  Preferences prefs;
  if (!prefs.begin(kNamespace, /*readOnly=*/false)) return false;
  const size_t written = prefs.putBytes(kKey, blob, sizeof(blob));
  prefs.end();
  return written == core::CAL_BLOB_SIZE;
}

void NvsCalStore::erase() {
  Preferences prefs;
  if (!prefs.begin(kNamespace, /*readOnly=*/false)) return;
  prefs.remove(kKey);
  prefs.end();
}

}  // namespace hal_esp32
