// hal::GridStore sobre NVS (Preferences): namespace "duelo", clave "grid", blob = core::gridSerialize.
#include <Preferences.h>
#include "gridmap.h"
#include "hal_esp32.h"

namespace {
constexpr const char* kNamespace = "duelo";
constexpr const char* kKey = "grid";
}  // namespace

namespace hal_esp32 {

bool NvsGridStore::load(core::GridCal& out) {
  Preferences prefs;
  if (!prefs.begin(kNamespace, /*readOnly=*/true)) return false;
  unsigned char blob[core::GRID_BLOB_SIZE];
  bool ok = false;
  if (prefs.getBytesLength(kKey) == core::GRID_BLOB_SIZE &&
      prefs.getBytes(kKey, blob, sizeof(blob)) == core::GRID_BLOB_SIZE) {
    ok = core::gridDeserialize(blob, core::GRID_BLOB_SIZE, out);   // verifica magia, versión y CRC, y recalcula el ajuste
  }
  prefs.end();
  return ok;
}

bool NvsGridStore::save(const core::GridCal& g) {
  unsigned char blob[core::GRID_BLOB_SIZE];
  if (core::gridSerialize(g, blob, sizeof(blob)) != core::GRID_BLOB_SIZE) return false;
  Preferences prefs;
  if (!prefs.begin(kNamespace, /*readOnly=*/false)) return false;
  const size_t written = prefs.putBytes(kKey, blob, sizeof(blob));
  prefs.end();
  return written == core::GRID_BLOB_SIZE;
}

void NvsGridStore::erase() {
  Preferences prefs;
  if (!prefs.begin(kNamespace, /*readOnly=*/false)) return;
  prefs.remove(kKey);
  prefs.end();
}

}  // namespace hal_esp32
