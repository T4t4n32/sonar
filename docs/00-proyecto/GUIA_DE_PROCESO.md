# Guía Rápida de Desarrollo y Proceso — SONAR (repo `I:\repository\Batalla Naval - Sonar\sonar`)

Sebastián y Jader Andrés Astaiza son los desarrolladores remotos para `lib/core` (lógica pura, cinemática, protocolo). Tú deseas que el repo sea la base firme de la programación y que todo el trabajo de documentación, código y testing se sane **al pelo**.

---

## 1. Mi Reparto de Trabajo (por semana / hitos)

| Fase | ¿Quién? | ¿Qué hace? | Entregables |
|---|---|---|---|
| I | Lucky (yo) | Teoría matemática + plano eléctrico + guía de integración + tablero LDR | `docs/01-diseno/TEORIA_CINEMATICA.md`, `docs/02-electronica/PLAN_ELECTRONICO.md` |
| II | Lucky (yo) | Implementación de `lib/core` + unidade de principios Unity + approx Testing via OpenCode CLI + simulación E2E en Python | Código fuente, tests unitarios y simulador de line-by-line |
| III | Sebas + Claude (local) | Hardware físico (LEDC + servos), wiring 3D y depuración visual | Firmware ESP32 cargado y probado |

### Mi workflow personal
1. Leer o ser auxiliado por la trayectoria de desarrollo deseada.
2. Scriptas si el resultado se integra en GitHub Actions.
3. Usa todos los skills del repositorio (`@t4os`, `@t4os-study-notes`, `@archite...[truncated]