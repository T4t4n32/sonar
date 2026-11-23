# Documentación de SONAR · Batalla Naval — índice maestro

**Empieza por [ESTADO.md](ESTADO.md)**: lo vigente, las decisiones, los conflictos entre fuentes y los pendientes. Todo lo del proyecto vive aquí (desde el 2026-11-08 ya no hay documentos sueltos en el vault).
Estados: **VIGENTE** · **PARCIAL** (útil, con partes superadas) · **HISTÓRICO** (referencia).

## 00 · Proyecto
| Documento | Qué es | Estado |
|---|---|---|
| [RUBRICA_Y_CUMPLIMIENTO](00-proyecto/RUBRICA_Y_CUMPLIMIENTO.md) | la rúbrica requisito por requisito y sus huecos | PARCIAL |
| [PENDIENTES](00-proyecto/PENDIENTES.md) | lista viva de tareas | VIGENTE |
| [REVISION_FINAL_2026-11-22](00-proyecto/REVISION_FINAL_2026-11-22.md) | **revisión final: rúbrica, 7 aclaraciones, franjas del lunes, checklist y borrador del correo** | VIGENTE |
| [PREGUNTAS_ALMARIO](00-proyecto/PREGUNTAS_ALMARIO.md) | la petición de casillas de 2 cm y el texto del correo | VIGENTE |
| [NOMBRE_DEL_PROYECTO](00-proyecto/NOMBRE_DEL_PROYECTO.md) | candidatos de nombre | VIGENTE |
| [GUIA_DE_PROCESO](00-proyecto/GUIA_DE_PROCESO.md) | reparto de trabajo y flujo (antes `GUIDA_DESVIO`) | PARCIAL |
| [EMPIEZA_AQUI_2026-11-03](00-proyecto/EMPIEZA_AQUI_2026-11-03.md) | versión mínima del 3-nov | HISTÓRICO |
| [PLAN_DE_TRABAJO_V1](00-proyecto/PLAN_DE_TRABAJO_V1.md) | plan de la versión grande | HISTÓRICO |

## 01 · Diseño
| Documento | Qué es | Estado |
|---|---|---|
| [FLUJO_JUEGO](01-diseno/FLUJO_JUEGO.md) | el juego completo dictado por Sebas y su evaluación técnica | VIGENTE (extra) |
| [ARQUITECTURA_UNIVERSAL](01-diseno/ARQUITECTURA_UNIVERSAL.md) | cómo se conecta cualquier celular, modos, seguridad del láser, fases | VIGENTE |
| [TORRETA_ABATIBLE](01-diseno/TORRETA_ABATIBLE.md) | torreta que se acuesta en el maletín: opciones A/B/C | VIGENTE |
| [DISENO_WEB](01-diseno/DISENO_WEB.md) | filosofía, motivos y tokens de la web | VIGENTE |
| [PLANOS_Y_MEDIDAS](01-diseno/PLANOS_Y_MEDIDAS.md) | hoja de cotas desde el dibujo a mano | VIGENTE (base) |
| [TEORIA_CINEMATICA](01-diseno/TEORIA_CINEMATICA.md) | cinemática inversa del apuntado | VIGENTE |
| [PLANO_SONAR_concepto_v2](01-diseno/planos/PLANO_SONAR_concepto_v2.pdf) | **plano conceptual del maletín (3 hojas A3, acotado): concepto, la base/bandeja y el asa oculta + placa SONAR** — para replicar en SolidWorks (se genera con `cad/generar_plano_v2.py`) | VIGENTE (propuesta) |
| [planos/](01-diseno/planos/) | plano de la carcasa anterior (PDF y vistas) | HISTÓRICO |
| [`cad/`](../cad/LEEME.md) | concepto 3D del maletín y el modelo SolidWorks | EN OBRA |

## 02 · Electrónica
| Documento | Qué es | Estado |
|---|---|---|
| [POTENCIA](02-electronica/POTENCIA.md) | cargas, fuente, batería opcional | VIGENTE |
| [PLAN_ELECTRONICO](02-electronica/PLAN_ELECTRONICO.md) | pines, distribución de potencia, matriz LDR | PARCIAL |
| [PINOUT](02-electronica/PINOUT.md) | tabla de pines del ESP32 | VIGENTE |
| [PROPUESTA_TABLERO_LDR](02-electronica/PROPUESTA_TABLERO_LDR.md) | tablero óptico con fotorresistencias | PARCIAL |
| [DISENO_DE_POTENCIA_V1](02-electronica/DISENO_DE_POTENCIA_V1.md) | cálculo de potencia de la versión grande | HISTÓRICO |

## 03 · Firmware y app
| Documento | Qué es | Estado |
|---|---|---|
| [PROTOCOLO](03-firmware-y-app/PROTOCOLO.md) | contrato de líneas de texto (v1 + v2) | VIGENTE |
| [CALIBRACION](03-firmware-y-app/CALIBRACION.md) | **cómo calibrar el apuntado a las 4 esquinas de la matriz (app o USB)** | VIGENTE |
| [APP_SONAR](03-firmware-y-app/APP_SONAR.md) | **plan de la app Android propia (APK): reglas del profesor 15-nov, pantallas, arquitectura, fases** | VIGENTE |
| [BRINGUP](03-firmware-y-app/BRINGUP.md) | puesta en marcha en banco, paso a paso | VIGENTE |
| [CONTROL1](03-firmware-y-app/CONTROL1.md) | lista para el control del 8-nov | VIGENTE |
| [APP_INVENTOR](03-firmware-y-app/APP_INVENTOR.md) | app con MIT App Inventor (descartada: la app es propia) | HISTÓRICO |
| [PRUEBAS_UNITARIAS](03-firmware-y-app/PRUEBAS_UNITARIAS.md) · [PRUEBAS_DE_INTEGRACION](03-firmware-y-app/PRUEBAS_DE_INTEGRACION.md) | planes de pruebas originales | PARCIAL |

## 04 · Compras
| Documento | Qué es | Estado |
|---|---|---|
| [LISTA_MERCADOLIBRE](04-compras/LISTA_MERCADOLIBRE.md) | lista por bloques A/B/C para Mercado Libre | VIGENTE |
| [COMPRAS_Y_PLAN_B](04-compras/COMPRAS_Y_PLAN_B.md) | Plan B con cámara y precios de Vistronica | VIGENTE |
| [LISTA_DE_COMPRAS_V1](04-compras/LISTA_DE_COMPRAS_V1.md) | lista de la versión grande | HISTÓRICO |

## 05 · Publicación
[LICENCIAS](05-publicacion/LICENCIAS.md) — MIT (código), CC BY-SA (docs), CERN-OHL (hardware). Informe: [`registro/preflight-2026-11-07.md`](../registro/preflight-2026-11-07.md).

## Archivo
[`archivo/`](archivo/): documentos superados (`BRIEF_WEB_SONAR`, `EVALUACION_PLAN_V1`).

## Fuera de docs/
[`branding/`](../branding/BRANDING.md) (logotipo, paleta, banner, guía de marca) · `registro/` (capturas y resultados de pruebas) · `cad/` (modelos) · `tools/analisis/` (cálculos de potencia, geometría y simulaciones, antes en el vault) · `tools/` (simulador, e2e, preflight, publicar, compras).
