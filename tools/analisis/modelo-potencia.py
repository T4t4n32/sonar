"""Modelo de potencia — Batalla Naval (2 modulos, cada uno: tablero 20x20 + torreta + ESP32).
Cada cifra lleva su origen: [HD] hoja de datos del fabricante revisada, [2a] fuente secundaria
(tienda/wiki), [SUP] supuesto de Lucky -> se mide en UT-HW. Ejecutar: python -I modelo-potencia.py
"""
import math

ETA = 0.90  # [SUP] eficiencia de los convertidores DC-DC
N_TILES, HALL_PER_TILE, LED_PER_MODULE = 4, 100, 400
HALL_TYP, HALL_MAX = 4.4e-3, 9.0e-3      # [HD] Allegro A3141-4: ICC 4,4 typ / 9,0 max mA (VCC = 8 V)
LED_STATIC, LED_FULL = 1.0e-3, 60e-3     # [2a] Adafruit: ~1 mA apagado, 60 mA a blanco pleno (3 x 20 mA)
LED_CAP = 2.0                            # [SUP] tope del limitador de firmware por modulo (A)
ESP_TYP, ESP_PEAK = 0.30, 0.50           # [HD] Tx 802.11b 240 mA; fuente recomendada >= 0,5 A
DFP_TYP, DFP_PEAK = 0.12, 0.50           # [2a] ~20 mA en espera / ~100 mA reproduciendo; pico del altavoz [SUP]
LASER_TYP, LASER_MAX = 0.03, 0.04        # [2a] KY-008: ~30 mA tipico, < 40 mA
LOGIC = 0.05                             # [SUP] 595, mux, buffers, pull-ups
SV_IDLE = 0.05                           # [SUP] servos sin PWM / retenidos sin carga
SV_RUN = 0.90 + 0.25                     # [2a] MG996R 900 mA a 6 V (hoja) + MG90S ~250 mA [SUP]
SV_STALL = 2.5 + 0.7                     # [2a] MG996R 2,5 A a 6 V (hoja) + MG90S ~0,7 A [SUP]
SCAN_DUTY = 0.026                        # [SUP] 100 canales x ~25 us por losa cada 100 ms


def rail5(master, scenario):
    dfp = {"reposo": 0.02, "tipico": DFP_TYP, "pico": DFP_PEAK}[scenario] if master else 0
    if scenario == "reposo":
        return 0.25 + HALL_TYP * HALL_PER_TILE * 0.0 + LED_PER_MODULE * LED_STATIC + LOGIC + dfp
    if scenario == "tipico":
        led = 1.0 + 0.0  # ~1 A: 166 azules al 10 %, 34 rojos al 20 %, estatico 0,4 A, flota propia
        return ESP_TYP + HALL_TYP * HALL_PER_TILE * SCAN_DUTY + led + LASER_TYP * 0.5 + LOGIC + dfp
    if scenario == "pico":
        return ESP_PEAK + HALL_MAX * HALL_PER_TILE + LED_CAP + LASER_MAX + LOGIC + dfp
    raise ValueError


def rail6(scenario, active):
    return {"reposo": SV_IDLE, "tipico": SV_RUN if active else SV_IDLE, "pico": SV_STALL if active else SV_IDLE}[scenario]


print("=== Carga por modulo (A) ===")
print(f"{'escenario':<10}{'5 V maestro':>13}{'5 V esclavo':>13}{'6 V activo':>12}{'6 V inactivo':>14}")
rows = {}
for s in ("reposo", "tipico", "pico"):
    m, e = rail5(True, s), rail5(False, s)
    a, i = rail6(s, True), rail6(s, False)
    rows[s] = (m, e, a, i)
    print(f"{s:<10}{m:>13.2f}{e:>13.2f}{a:>12.2f}{i:>14.2f}")

print("\n=== Entrada de 12 V (ambos modulos; solo una torreta se mueve a la vez) ===")
inp = {}
for s, (m, e, a, i) in rows.items():
    p = (5 * (m + e) + 6 * (a + i)) / ETA
    inp[s] = p
    print(f"{s:<10} P = {p:5.1f} W   I = {p/12:4.2f} A")

pico_i = inp["pico"] / 12
print(f"\nAdaptador de 12 V: >= {pico_i/0.8:.1f} A (pico al 80 % de su capacidad)")
m, e, a, i = rows["pico"]
print(f"Convertidor 5 V : pico {max(m, e):.2f} A -> capacidad >= {max(m, e)/0.75:.1f} A (75 % de carga)")
print(f"Convertidor 6 V : stall {a:.2f} A -> capacidad >= {a/0.75:.1f} A (75 % de carga)")
mod_i = (5 * m + 6 * a) / ETA / 12
print(f"Fusible 12 V por modulo: pico {mod_i:.2f} A -> >= {mod_i*1.25:.1f} A lento")

print("\n=== Sin compuerta de Hall (todos alimentados siempre), por modulo ===")
hall_t, hall_m = HALL_TYP * HALL_PER_TILE * N_TILES, HALL_MAX * HALL_PER_TILE * N_TILES
print(f"Hall continuo: tipico {hall_t:.2f} A, maximo {hall_m:.2f} A (con compuerta: 0,44 / 0,90 A solo mientras se escanea una losa)")
print(f"Pico 5 V maestro sin compuerta: {rail5(True,'pico') - HALL_MAX*HALL_PER_TILE + hall_m:.2f} A (con compuerta {rail5(True,'pico'):.2f} A)")

print("\n=== Comparacion con el V1 (un tablero) ===")
v1 = 0.24 + 1.5 + 2.0 + 0.03 + 0.10
real = 0.24 + 1.5 + 2.0 + 0.03 + HALL_TYP * 400 + 0.10
print(f"V1 declarado: {v1+0.0:.2f} A (el V1 dice 3,87 A)   |   con Hall = 4,4 mA: {real:.2f} A   |   con Hall = 9 mA: {real - HALL_TYP*400 + HALL_MAX*400:.2f} A")

print("\n=== Pistas de cobre, 1 oz exterior (IPC-2221, subida de 10 C) ===")
def width_mm(i, dt=10, oz=1):
    area = (i / (0.048 * dt ** 0.44)) ** (1 / 0.725)  # mil^2
    return area / (1.378 * oz) * 0.0254
for i in (0.5, 1.0, 1.4, 2.0, 3.0):
    print(f"  {i:.1f} A -> {width_mm(i):.2f} mm")

print("\n=== Caidas de tension ===")
print(f"  AWG18 6,4 mOhm/m: 3,6 A x 1,0 m ida y vuelta = {3.6*0.0064*1.0*1000:.0f} mV")
print(f"  Cable de servo ~28 AWG (~0,2 ohm/m): MG996R 2,5 A, 0,3 m ida y vuelta = {2.5*0.2*0.6*1000:.0f} mV ; a 0,9 A = {0.9*0.2*0.6*1000:.0f} mV")
rcu = 0.49e-3  # ohm/cuadro, cobre de 1 oz
print(f"  Bus 5 V de una losa: pista 1 mm x 200 mm = {200*rcu*1000:.0f} mOhm; carga repartida 0,5 A -> caida al final {0.5*200*rcu/2*1000:.0f} mV")
