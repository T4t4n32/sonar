# Guion del video — «MISIÓN: CERO PUNTO DOS»

**Duración objetivo: 5:30 a 6:00.** Formato: informe militar con humor. Reparto: **Sebas abre (0:35) y cierra (0:35); [Compañero] explica todo el centro (≈ 4:15).**
Idea del chiste: las 0,2 décimas que bajaron por estética son «las bajas de la misión»; el video es la operación para recuperarlas explicando bien el proyecto.
Tono: serio por fuera, gracioso por dentro. Nadie se ríe en cámara. Frases cortas, dichas con voz de radio.

> **Regla de oro:** [Compañero] no lee de memoria; cuenta con sus palabras mientras se ve el hardware o la pantalla. Las frases de abajo son un guion de apoyo, no un texto sagrado. Todo lo que se diga debe ser verdad y verse en pantalla.

---

## 0. Apertura — Sebas (0:35)
**Imagen:** fondo oscuro o pared lisa, gorra o chaleco, el proyecto cubierto con una tela. Título en pantalla: **MISIÓN: CERO PUNTO DOS** (letras tipo máquina de escribir). Sonido de radio o redoble corto.

> **Sebas (en pose de comandante):** «Informe de misión. Operación: **Cero Punto Dos**. Situación: la sustentación fue un éxito, pero las **bajas** fueron dos décimas de estética. El alto mando pidió una explicación completa del sistema. Objetivo: **recuperar el honor del escuadrón** explicando cómo funciona SONAR, nuestra batalla naval. Para eso entra en acción mi compañero, **[Nombre]**, jefe de explicación técnica. Soldado, tiene la palabra.»

**Corte a [Compañero] saludando militarmente.**

---

## 1. Qué es SONAR y qué pide la consigna — [Compañero] (0:30)
**Imagen:** el proyecto completo, destapado. Texto en pantalla: «Lo que pide la consigna».

> «A la orden. SONAR es una **batalla naval con láser**. La consigna pide una estación de ataque y un tablero de **30 por 30 cm**, con una matriz de **20 por 20 cm**, elevado **5 cm**. Los disparos se mandan **desde el celular por Bluetooth** con una **app propia**, en formato **(x, y)**, y cada disparo hace un **sonido**. Y hay un **test de 5 posiciones**. Vamos por partes.»

*Apoyo en pantalla:* mostrar el tablero y señalar la matriz de 20×20 y los 5 cm de elevación.

---

## 2. El hardware (la «tropa») — [Compañero] (0:45)
**Imagen:** primer plano de cada pieza, con rótulo al señalarla.

> «Esta es la tropa: un **ESP32**, que es el cerebro y trae Bluetooth. **Dos servos**: uno gira de lado a lado, el **pan**, y otro sube y baja, el **tilt**. Montado encima va un **láser rojo** de 650 nanómetros. Los servos van con **6 voltios de pilas** y el ESP32 con su propio USB: así los servos no le roban corriente al cerebro. Todos comparten la **tierra, el GND**, y hay un **capacitor de 1000 microfaradios** junto a los servos para que no se caiga el voltaje cuando arrancan.»

*Rótulos:* ESP32 · Servo pan (GPIO 18) · Servo tilt (GPIO 19) · Láser (GPIO 23) · Pilas 6 V · Capacitor 1000 µF · Zumbador (GPIO 21, si está conectado).
*Mostrar solo lo que realmente está montado. Si el zumbador no está, no lo nombres.*

---

## 3. Cómo apunta con precisión (la «calibración») — [Compañero] (1:00)
**Imagen:** la hoja impresa pegada; el láser apuntando a una esquina; la pantalla de «Calibrar apuntado» de la app.

> «El reto es que el láser caiga en la casilla exacta de 1 centímetro. Cada montaje queda distinto, así que no confiamos en medir distancias con regla. Hacemos esto: **apuntamos el láser a las 4 esquinas** de la matriz y el sistema **memoriza los ángulos** de los servos en cada una. Con esas cuatro esquinas, el ESP32 **calcula por matemáticas las 400 casillas** del tablero. Se llama una **homografía**: es como estirar una cuadrícula para que encaje en el montaje real. Después apuntamos al centro como **punto de control**: si el error es menor a medio grado, está bien calibrado. Todo se guarda en la memoria del ESP32 y **no se pierde al apagarlo**.»

*Demo corta (10 s):* tocar una casilla distinta en la app y que el láser caiga en ella. Rótulo: «400 casillas, 4 esquinas».
*Si te preguntan «¿por qué no solo calcular?»:* «Porque la montura nunca queda perfecta; medir las esquinas cancela esos errores».

---

## 4. Movimiento suave y seguridad — [Compañero] (0:40)
**Imagen:** servos moviéndose; la app con el botón **STOP**.

> «Los servos no se mueven de golpe: **arrancan y frenan suave**, y los dos se mueven a la vez. El último tramo siempre lo hacen **despacio y subiendo**, para eliminar el juego de los engranes y caer siempre en el mismo punto. Y la seguridad: el **láser nunca está encendido mientras un servo se mueve**. Hay un botón **STOP** que lo apaga al instante, y si se olvida encendido, **se apaga solo**. Después de cada disparo el láser queda encendido para que el profesor lo vea bien, hasta el siguiente movimiento.»

---

## 5. La app y el protocolo — [Compañero] (1:00)
**Imagen:** grabación de pantalla del celular: conectar con **SONAR-A**, tablero 20×20, apuntar, disparar, «¿Le dio?», hundido.

> «La app es **propia**: la hicimos nosotros. Se conecta por Bluetooth al módulo, que se llama **SONAR-A**. Cada disparo viaja como un texto simple: **(x, y)**, primero la equis y luego la ye, como pidió el profesor. El ESP32 lo recibe, calcula los ángulos, mueve los servos y enciende el láser con un **pitido**. La app pregunta **“¿Le dio?”** y el **testigo** responde. Para ir rápido, traemos **cinco plantillas de flota** numeradas: tres embarcaciones de 2 casillas y dos submarinos de 4. La app lleva la cuenta, y si se toca **cualquier casilla** de un barco, ese barco se hunde y la app dice **dónde estaba**, tal como dijo el profesor. También hay un botón para **cambiar de plantilla** y empezar una partida nueva.»

*En pantalla:* mostrar la pestaña Partida con los botones de plantilla 1–5 y la hoja de bolsillo con la plantilla pintada.

---

## 6. Demostración del test — [Compañero] (0:35)
**Imagen:** plano general del montaje y la pantalla del celular al lado.

> «Y ahora la prueba: el **test de 5 posiciones**. Son las cuatro esquinas y el centro. Pulso **TEST**…»

*(Se ve el láser recorriendo las 5 posiciones sobre la hoja; contar en voz alta cada una.)*

> «…y el láser cae en las cinco. Test completo.»

*Si falla una posición, **no cortes ni repitas en secreto**: di «el sistema guarda este error, lo corregimos recalibrando» y repite. Es más honesto y explica mejor.*

---

## 7. Cierre — Sebas (0:35)
**Imagen:** Sebas de nuevo en pose de comandante; el proyecto detrás.

> **Sebas:** «Gracias, soldado. Informe final: el sistema **apunta, dispara, suena y se explica solo**. **Bajas de la misión:** cero punto dos décimas, en estética. **Daños al honor:** reparados. Mensaje al alto mando: **la próxima vez, más cinta y menos cables sueltos**.»
> **[Compañero]:** «¡Señor, sí, señor!»
> **Sebas:** «**Misión cumplida.** Cambio y fuera.»

*Final:* ambos saludan; pantalla negra con «MISIÓN CUMPLIDA — SONAR · Batalla Naval · [Nombres]».

---

## Lista de planos (grabar todo suelto y luego montar)
| # | Plano | Quién | Duración |
|---|---|---|---|
| 1 | Apertura con título | Sebas | 0:35 |
| 2 | Presentación del proyecto y consigna | [Compañero] | 0:30 |
| 3 | Primeros planos de piezas (sin hablar, para tapar con voz) | — | 0:30 |
| 4 | Explicación del hardware | [Compañero] | 0:45 |
| 5 | Calibración: láser en las esquinas + pantalla de la app | [Compañero] | 1:00 |
| 6 | Servos moviéndose + botón STOP | [Compañero] | 0:40 |
| 7 | Grabación de pantalla de la app (conexión, disparo, hundido, plantillas) | [Compañero] | 1:00 |
| 8 | Test de 5 posiciones, plano general | [Compañero] | 0:35 |
| 9 | Cierre | Sebas + [Compañero] | 0:35 |

## Para [Compañero]: hoja de repaso (preguntas que pueden aparecer)
1. **¿Qué hace el ESP32?** Recibe `(x,y)` por Bluetooth, calcula los ángulos de dos servos, los mueve y enciende el láser con un pitido.
2. **¿Por qué los servos van aparte?** Consumen mucha corriente al arrancar; si salieran del ESP32 lo reiniciarían. Van con 6 V de pilas y GND común.
3. **¿Para qué el capacitor?** Amortigua el pico de corriente del arranque de los servos.
4. **¿Cómo sabe adónde apuntar?** Se calibra apuntando a las 4 esquinas; el módulo calcula las 400 casillas con una homografía.
5. **¿Qué es el punto de control?** El centro (11,11): se compara lo medido con lo calculado; el error dice qué tan buena es la calibración.
6. **¿Por qué el último tramo es lento y subiendo?** Para eliminar la holgura de los engranes y que siempre llegue por el mismo lado.
7. **¿Es seguro el láser?** Nunca está encendido mientras se mueven los servos; `STOP` lo apaga al instante; se apaga solo si se olvida.
8. **¿Qué manda la app?** Un texto `(x,y)`, primero x y luego y.
9. **¿Qué es el test de 5 posiciones?** Las cuatro esquinas y el centro, en el propio sistema.
10. **¿Qué es original?** Firmware en C++ con pruebas automáticas, app propia y protocolo propio. Cualquier copia se nota en el historial de commits.
11. **¿Qué pasa si el rival usa otra app?** Mientras mande `(x,y)` por Bluetooth, nuestro módulo la acepta, incluso sin salto de línea.
12. **¿Qué mejorarían?** La estética (cableado y acabado) y registrar más puntos de calibración desde la app.

## Consejos de grabación
- Luz de frente, celular horizontal, **audio limpio** (la voz importa más que la imagen). Grabar en un lugar sin eco.
- Cada plano de [Compañero] debe mostrar **lo que está explicando** (la pieza o la pantalla), no solo su cara.
- Para la pantalla del celular: usar la grabación de pantalla (o `scrcpy`) y luego poner la voz encima.
- Subtítulos cortos en los términos técnicos (homografía, GPIO, GND, SPP).
- Música militar suave solo en la apertura y el cierre; en el centro, silencio.
- Dejar 3 s de silencio antes y después de cada plano para cortar fácil.
- **Los dos deben aparecer y hablar**: la rúbrica pide que participen los dos desarrolladores.
- Antes de grabar: pilas nuevas, firmware 0.2.0 cargado, calibración guardada, `TEST` funcionando dos veces seguidas.
