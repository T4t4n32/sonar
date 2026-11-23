"""Genera el PDF del guion del video «MISIÓN: CERO PUNTO DOS» (guion narrativo + plan de producción).
Uso: uv run --with reportlab python tools/guion_video_pdf.py [salida.pdf]
"""
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

OLIVA = colors.HexColor("#3E4A2B")
OLIVA_CLARO = colors.HexColor("#E7EAD9")
ARENA = colors.HexColor("#F4EFE0")
ROJO = colors.HexColor("#8C2B22")
GRIS = colors.HexColor("#444444")
ORO = colors.HexColor("#B8892B")

base = ParagraphStyle("base", fontName="Helvetica", fontSize=9.6, leading=13.4, textColor=colors.HexColor("#1B1B1B"))
H1 = ParagraphStyle("H1", parent=base, fontName="Courier-Bold", fontSize=17, leading=21, textColor=OLIVA, spaceBefore=4, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=base, fontName="Courier-Bold", fontSize=12, leading=15, textColor=OLIVA, spaceBefore=10, spaceAfter=3)
H3 = ParagraphStyle("H3", parent=base, fontName="Helvetica-Bold", fontSize=9.6, textColor=ROJO, spaceBefore=6, spaceAfter=1)
small = ParagraphStyle("small", parent=base, fontSize=8.4, leading=11.4, textColor=GRIS)
lyric = ParagraphStyle("lyric", parent=base, fontName="Helvetica-Oblique", fontSize=10.2, leading=14.6)
cellp = ParagraphStyle("cell", parent=base, fontSize=8.4, leading=11)
cellb = ParagraphStyle("cellb", parent=cellp, fontName="Helvetica-Bold")
center = ParagraphStyle("center", parent=base, alignment=TA_CENTER)


def P(t, s=base):
    return Paragraph(t, s)


def escena(num, titulo, tiempo, quien):
    t = Table([[P(f"<font color='white'><b>{num}</b></font>", ParagraphStyle("n", parent=base, fontName="Courier-Bold", fontSize=11, leading=13, alignment=TA_CENTER)),
                P(f"<b>{titulo}</b>", ParagraphStyle("t", parent=base, fontName="Courier-Bold", fontSize=11.5, leading=14, textColor=OLIVA)),
                P(f"{tiempo} · {quien}", ParagraphStyle("r", parent=small, alignment=2))]],
              colWidths=[12 * mm, 100 * mm, 62 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), OLIVA), ("BACKGROUND", (1, 0), (2, 0), OLIVA_CLARO),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def dialogo(rol, texto, estilo=lyric):
    t = Table([[P(f"<b>{rol}</b>", ParagraphStyle("rl", parent=small, textColor=ROJO, fontName="Helvetica-Bold")), P(texto, estilo)]],
              colWidths=[26 * mm, 148 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBEFORE", (1, 0), (1, 0), 1.6, ORO),
                           ("LEFTPADDING", (1, 0), (1, 0), 8), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t


def caja(titulo, texto, fondo=ARENA, borde=OLIVA):
    t = Table([[P(f"<b>{titulo}</b><br/>{texto}", cellp)]], colWidths=[174 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fondo), ("BOX", (0, 0), (-1, -1), 0.8, borde),
                           ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def tecnica(texto):
    return caja("TRADUCCIÓN TÉCNICA · decirla con claridad, tal cual (esto es lo que evalúa el General)", texto, fondo=colors.HexColor("#FFF6D8"), borde=ORO)


def tabla(filas, anchos, cab=True):
    data = [[P(c, cellb if (cab and i == 0) else cellp) for c in f] for i, f in enumerate(filas)]
    t = Table(data, colWidths=[a * mm for a in anchos], repeatRows=1 if cab else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA38A")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if cab:
        st += [("BACKGROUND", (0, 0), (-1, 0), OLIVA_CLARO)]
    t.setStyle(TableStyle(st))
    return t


def portada(c, doc):
    w, h = letter
    c.saveState()
    c.setFillColor(colors.HexColor("#1F2615"))
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setStrokeColor(ORO)
    c.setLineWidth(1.2)
    c.rect(14 * mm, 14 * mm, w - 28 * mm, h - 28 * mm, stroke=1, fill=0)
    c.setFillColor(ORO)
    c.setFont("Courier-Bold", 10)
    c.drawCentredString(w / 2, h - 34 * mm, "E S C U A D R Ó N   S O N A R   ·   M A T E R I A L   R E S E R V A D O")
    c.setFillColor(colors.HexColor("#EFE9D8"))
    c.setFont("Courier-Bold", 40)
    c.drawCentredString(w / 2, h - 95 * mm, "MISIÓN:")
    c.setFont("Courier-Bold", 46)
    c.drawCentredString(w / 2, h - 118 * mm, "CERO PUNTO DOS")
    c.setStrokeColor(ROJO)
    c.setLineWidth(3)
    c.line(w / 2 - 60 * mm, h - 126 * mm, w / 2 + 60 * mm, h - 126 * mm)
    c.setFillColor(colors.HexColor("#CFC9B4"))
    c.setFont("Helvetica-Oblique", 13)
    c.drawCentredString(w / 2, h - 142 * mm, "«Hay números que no se pierden: esperan.»")
    c.setFont("Helvetica", 10.5)
    c.drawCentredString(w / 2, h - 170 * mm, "Guion narrativo y plan de producción")
    c.drawCentredString(w / 2, h - 177 * mm, "Video explicativo · SONAR · Batalla Naval")
    c.setFillColor(ORO)
    c.setFont("Courier-Bold", 10)
    c.drawCentredString(w / 2, 34 * mm, "OBJETIVO: EL CINCO SAGRADO  ·  PENDIENTE: 0,2")
    c.setFillColor(colors.HexColor("#CFC9B4"))
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(w / 2, 26 * mm, "Orden dictada por el General · Ejecuta: Capitán ALFA y Sargento BRAVO")
    c.restoreState()


def interior(c, doc):
    w, h = letter
    c.saveState()
    c.setFillColor(OLIVA)
    c.rect(0, h - 11 * mm, w, 11 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#EFE9D8"))
    c.setFont("Courier-Bold", 8.5)
    c.drawString(18 * mm, h - 7.2 * mm, "MISIÓN: CERO PUNTO DOS")
    c.drawRightString(w - 18 * mm, h - 7.2 * mm, f"Escuadrón SONAR · pág. {doc.page}")
    c.restoreState()


def build(path):
    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=16 * mm,
                            title="MISIÓN: CERO PUNTO DOS - guion y producción", author="Escuadrón SONAR")
    S = []
    S += [Spacer(1, 1), PageBreak()]

    # ---------------------------------------------------------------- 1. Premisa
    S += [P("1 · La premisa", H1)]
    S += [P("Un escuadrón pequeño libró «la batalla del corte final» y volvió con <b>4,8</b> en el morral. Dos décimas se quedaron atrás, "
            "caídas en la <b>Trinchera de la Estética</b>. El <b>General</b> —que ve lejos y pregunta bien— no pidió excusas: dictó una sola orden, "
            "<b>explicar la campaña completa ante cámara</b>. Porque este escuadrón no persigue un número: persigue <b>el Cinco Sagrado</b>.", lyric)]
    S += [Spacer(1, 4), P("<b>Cómo funciona el truco.</b> Todo el video es una <i>carta de guerra</i>: suena a épica militar, pero cada metáfora es una explicación técnica "
                          "exacta. Después de cada escena hay una <b>traducción técnica</b> en una caja amarilla: esa frase se dice en cámara, <i>tal cual</i>, "
                          "para que no quede duda de que el Sargento domina el sistema. La lírica es el envoltorio; la ingeniería es el contenido.")]
    S += [Spacer(1, 6), P("Reparto y rangos", H2)]
    S += [tabla([["Rol", "Quién", "En cámara", "Nota"],
                 ["<b>Capitán ALFA</b>", "Sebas", "Apertura (0:40) y cierre (0:45), más voz en off del «Diario de campaña»", "Mando, sobriedad, humor seco"],
                 ["<b>Sargento BRAVO</b>", "[Compañero]", "El informe de campo: unos 4:10 de explicación técnica", "El protagonista del video"],
                 ["<b>El General</b>", "(el profesor)", "Nunca sale en cámara: solo existe como <b>sobre sellado</b> y como voz de radio (la lee Sebas)", "Siempre con respeto; el General tiene la última palabra"],
                 ["<b>El Cinco Sagrado</b>", "—", "El objetivo: la nota 5,0", "Se nombra con solemnidad"],
                 ["<b>Las dos Esquirlas</b>", "—", "Las 0,2 décimas que faltan", "El título de la misión"]],
                [32, 24, 78, 40])]
    S += [Spacer(1, 6), P("Glosario: la metáfora y lo que significa de verdad", H2)]
    S += [tabla([["En el relato", "En la realidad (decir esto también)"],
                 ["El Campo", "Tablero de 30×30 cm con la matriz de 20×20 cm (400 casillas de 1 cm), elevado 5 cm"],
                 ["El Cerebro", "El ESP32: recibe las órdenes por Bluetooth, calcula y manda a los servos"],
                 ["Las dos Torres", "Dos servos: el <b>pan</b> gira de lado a lado, el <b>tilt</b> sube y baja"],
                 ["El Ojo", "El láser rojo de 650 nm"],
                 ["El Sustento", "6 V de pilas para los servos; el ESP32 va aparte por USB; GND común; capacitor de 1000 µF"],
                 ["El Mapa de las Cuatro Esquinas", "Calibración: apuntar a las 4 esquinas y calcular las 400 casillas (homografía); el centro es el punto de control"],
                 ["El Pulso Sereno", "Movimiento suave y sincronizado; remate lento subiendo; láser apagado mientras se mueve; STOP"],
                 ["La Radio", "Bluetooth (SPP) y la app propia; el módulo se llama SONAR-A; el disparo viaja como (x, y)"],
                 ["El Juez de campo", "El testigo que responde «¿le dio?»"],
                 ["Las Cartas de flota", "Las 5 plantillas numeradas: 3 embarcaciones de 2 casillas y 2 submarinos de 4"],
                 ["La Prueba de Fuego", "El test de 5 posiciones: las 4 esquinas y el centro"]],
                [52, 122])]

    S += [PageBreak(), P("2 · El guion", H1)]
    S += [P("<b>Duración objetivo: 6:00 como máximo.</b> Nunca leer de memoria: se cuenta con las propias palabras mientras se ve la pieza o la pantalla. "
            "Las frases son una guía; lo que no puede cambiar son las traducciones técnicas.", small), Spacer(1, 4)]

    S += [escena("0", "FRÍO DE APERTURA · EL SOBRE", "0:15", "Sebas (voz)")]
    S += [P("<b>Imagen:</b> pantalla negra. Estática de radio. Se ilumina un <b>sobre sellado</b> sobre una mesa con tela verde oliva. Un sello rojo: «ORDEN DEL GENERAL». "
            "Una mano rompe el sello (plano detalle). <b>Sonido:</b> estática, un pitido de radio, un tambor bajo.", small)]
    S += [dialogo("VOZ DEL GENERAL<br/>(Sebas, grave, con filtro de radio)",
                  "«Escuadrón SONAR. Hay números que no se pierden: esperan. Dos décimas quedaron en el campo de la Estética. "
                  "El Cinco no se negocia. Tienen un informe que dar.»")]

    S += [Spacer(1, 6), escena("I", "LA ORDEN", "0:40", "Sebas · Capitán Alfa")]
    S += [P("<b>Imagen:</b> plano medio de Sebas, de uniforme improvisado, con la linterna de frente iluminando el sobre abierto. Título en cartón: <b>«ACTO I · LA ORDEN»</b>. "
            "Detrás, el proyecto cubierto por una tela.", small)]
    S += [dialogo("CAPITÁN ALFA",
                  "«Escuadrón SONAR, aquí el Capitán Alfa. Hace unos días libramos la batalla del corte final. Salimos con la frente en alto y <b>cuatro coma ocho</b> en el morral. "
                  "Dos décimas se quedaron atrás, caídas en la Trinchera de la Estética. El General —que ve lejos y pregunta bien— dictó una sola orden: "
                  "<b>explicar la campaña, completa, ante cámara.</b> Porque este escuadrón no persigue un número. Persigue <b>el Cinco Sagrado</b>. "
                  "No pido venganza: pido un informe. Sargento Bravo… el frente es suyo.»")]
    S += [dialogo("SARGENTO BRAVO", "(entra a cuadro, saludo militar, la tela cae y aparece el montaje) «A la orden, Capitán. Comenzando el informe de campo.»")]

    S += [Spacer(1, 6), P("ACTO II · EL INFORME DE CAMPO (Sargento Bravo)", H2)]
    S += [P("<b>Entre escenas:</b> la «voz del Capitán» (Sebas, 5 s, sobre imágenes sueltas): una línea del <b>Diario de campaña</b>, escrita abajo, escena por escena. "
            "Son opcionales; si el tiempo aprieta, se cortan.", small), Spacer(1, 4)]

    S += [KeepTogether([escena("1", "EL CAMPO", "0:30", "Bravo"),
                        P("<b>Diario:</b> <i>«El terreno es honesto. Solo miente quien lo mide mal.»</i>", small),
                        P("<b>Imagen:</b> plano cenital (desde arriba) del tablero; después plano medio de Bravo señalando la matriz y los 5 cm de elevación con una regla.", small),
                        dialogo("BRAVO", "«Todo ejército necesita un campo. El nuestro mide veinte por veinte: cuatrocientos cuadros de un centímetro, tendidos sobre un tablero de treinta, "
                                         "a cinco centímetros del suelo… para que el agua no moje la pólvora.»"),
                        tecnica("«Es la matriz de 20×20 cm, casillas de 1 cm, dentro del tablero de 30×30 cm, elevado 5 cm, como pide la consigna. Los disparos se mandan desde el celular "
                                "por Bluetooth, con una app propia, en formato (x, y).»")])]

    S += [Spacer(1, 2), KeepTogether([escena("2", "LA TROPA", "0:45", "Bravo"),
                                      P("<b>Diario:</b> <i>«Una tropa pequeña, bien alimentada, vale por un regimiento.»</i>", small),
                                      P("<b>Imagen:</b> primeros planos de cada pieza al nombrarla (con un rótulo de cartón o texto): Cerebro, Torres, Ojo, pilas, capacitor.", small),
                                      dialogo("BRAVO", "«Esta es la tropa. El <b>Cerebro</b>, que piensa y escucha por radio. Las <b>dos Torres</b>: una gira de lado a lado, la otra sube y baja. "
                                                       "El <b>Ojo</b>, que mira donde se le ordena. Y el <b>Sustento</b>: seis voltios de pilas para las Torres, porque las Torres comen mucho "
                                                       "y no se le quita el pan al Cerebro. Todos comparten la misma tierra, y una reserva de mil microfaradios guarda el aliento "
                                                       "para cuando las Torres arrancan.»"),
                                      tecnica("«El Cerebro es un ESP32, que trae Bluetooth. Los dos servos son el pan, que gira, y el tilt, que sube y baja. El Ojo es un láser rojo de 650 nanómetros. "
                                              "Los servos van con 6 voltios de pilas y el ESP32 por su propio USB, para que los servos no lo reinicien. Todos comparten el GND, y el capacitor de "
                                              "1000 microfaradios amortigua el pico de corriente cuando los servos arrancan.»")])]

    S += [Spacer(1, 2), KeepTogether([escena("3", "EL MAPA DE LAS CUATRO ESQUINAS", "1:00", "Bravo"),
                                      P("<b>Diario:</b> <i>«Ningún mapa se dibuja desde la oficina. Se camina el terreno.»</i>", small),
                                      P("<b>Imagen:</b> el láser tocando una esquina de la hoja impresa; luego la pantalla de <b>Calibrar apuntado</b> en la app; al final, un disparo a una casilla cualquiera y el láser cayendo en ella.", small),
                                      dialogo("BRAVO", "«Enviamos al Ojo a las cuatro esquinas del campo. En cada una, las Torres memorizan su ángulo. Con cuatro puntos, el Cerebro dibuja el mapa completo: "
                                                       "cuatrocientos cuadros, sin medir una sola distancia con regla. Después, la prueba de honor: el centro. "
                                                       "Si el Ojo cae donde el mapa dijo, el mapa es leal. Y el mapa se guarda en la memoria del Cerebro: apague el campamento, el mapa sigue ahí.»"),
                                      tecnica("«Es la calibración: apuntamos el láser a las cuatro esquinas de la matriz y el módulo guarda los ángulos de los servos. Con ellos calcula una homografía, "
                                              "que es una transformación que convierte cada casilla (x, y) en sus dos ángulos. El centro es el punto de control: si el error es menor a medio grado, "
                                              "está bien calibrado. Todo queda guardado en la memoria del ESP32 y no se pierde al apagarlo.»")])]

    S += [Spacer(1, 2), KeepTogether([escena("4", "EL PULSO SERENO", "0:40", "Bravo"),
                                      P("<b>Diario:</b> <i>«Quien dispara con la mano temblorosa, falla dos veces: la primera al apuntar.»</i>", small),
                                      P("<b>Imagen:</b> las Torres moviéndose en cámara lenta; el dedo sobre el botón STOP de la app; el láser apagándose.", small),
                                      dialogo("BRAVO", "«El Ojo no se abre mientras las Torres caminan: solo mira cuando todo está quieto. Las Torres no corren: arrancan despacio, frenan despacio, "
                                                       "y el último paso siempre lo dan subiendo, para llegar siempre por el mismo lado. Y si algo sale mal, una sola palabra: <b>STOP</b>. "
                                                       "El Ojo se cierra. Si el centinela se duerme, el Ojo se cierra solo.»"),
                                      tecnica("«Los dos servos se mueven a la vez con arranque y frenado suave. El último tramo es lento y siempre subiendo, para eliminar el juego de los engranes y caer siempre en el mismo punto. "
                                              "El láser nunca está encendido mientras un servo se mueve. STOP lo apaga al instante y, si se olvida encendido, se apaga solo. "
                                              "Después de cada disparo el láser queda encendido hasta el siguiente movimiento, para que se vea bien.»")])]

    S += [Spacer(1, 2), KeepTogether([escena("5", "LA RADIO", "1:00", "Bravo"),
                                      P("<b>Diario:</b> <i>«Una orden clara vale más que mil soldados.»</i>", small),
                                      P("<b>Imagen:</b> grabación de pantalla del celular (conexión a SONAR-A, tablero, disparo, «¿Le dio?», barco hundido, pestaña Partida con las plantillas 1–5); "
                                        "plano de la hoja de bolsillo con la plantilla pintada.", small),
                                      dialogo("BRAVO", "«Las órdenes viajan por radio, en clave sencilla: dos números entre paréntesis, primero la equis y luego la ye. Nuestro módulo se llama <b>SONAR-A</b> y escucha. "
                                                       "Cada disparo suena. El Juez de campo responde la pregunta de siempre: <i>¿le dio?</i> Y para no perder tiempo en el frente, el escuadrón lleva "
                                                       "<b>cinco Cartas de flota</b>, numeradas: tres embarcaciones de dos casillas y dos submarinos de cuatro. La primera partida usa la carta uno; la siguiente, la dos. "
                                                       "Y rige la ley del General: con tocar una sola casilla del barco, el barco cae, y la radio dice dónde estaba.»"),
                                      tecnica("«La app es propia. Se conecta por Bluetooth al módulo, que se llama SONAR-A. Cada disparo viaja como un texto (x, y), primero x y luego y. El ESP32 calcula los ángulos, "
                                              "mueve los servos y enciende el láser con un pitido. La app pregunta «¿le dio?» y el testigo responde. Hay cinco plantillas de flota numeradas, "
                                              "y la app rota entre ellas en cada partida. Si se toca cualquier casilla de un barco, ese barco se hunde y la app muestra dónde estaba.»")])]

    S += [Spacer(1, 2), KeepTogether([escena("6", "LA PRUEBA DE FUEGO", "0:35", "Bravo")  ,
                                      P("<b>Diario:</b> <i>«Al final, todo mapa se juzga en el terreno.»</i>", small),
                                      P("<b>Imagen:</b> plano general: montaje, hoja y celular en el mismo cuadro; luego plano detalle de cada punto de láser sobre la esquina. Contar cada posición en voz alta.", small),
                                      dialogo("BRAVO", "«Cinco posiciones: las cuatro esquinas y el centro. Sargento Bravo reportando… (pulsa TEST) …una… dos… tres… cuatro… cinco. "
                                                       "El Ojo estuvo donde debía. Prueba superada.»"),
                                      tecnica("«El test de 5 posiciones lanza el láser a las cuatro esquinas y al centro, en el propio sistema tablero-estación, como pide la rúbrica.»"),
                                      caja("SI UNA POSICIÓN FALLA", "No cortar ni repetir a escondidas: decir «el sistema guarda ese error; se corrige recalibrando» y repetir. Explica mejor y es más honesto.",
                                           fondo=colors.HexColor("#FBE9E7"), borde=ROJO)])]

    S += [Spacer(1, 2), escena("III", "EL REGRESO", "0:45", "Alfa y Bravo")]
    S += [P("<b>Imagen:</b> los dos frente al montaje, en plano medio; luz más cálida que en el resto del video (amanecer). Alfa sostiene el sobre. "
            "Final: plano fijo, ambos saludan; cierre en negro con el sello.", small)]
    S += [dialogo("CAPITÁN ALFA", "«Sargento, ¿con cuánto volvemos del frente?»"),
          dialogo("SARGENTO BRAVO", "«Con cuatro coma ocho, Capitán… y con el informe completo.»"),
          dialogo("CAPITÁN ALFA", "«Cuatro coma ocho… y dos esquirlas por recoger.»"),
          dialogo("SARGENTO BRAVO", "«Cero coma dos, Capitán. Lo que separa a este escuadrón del Cinco Sagrado.»"),
          dialogo("CAPITÁN ALFA", "«El Cinco no se toma. Se merece. Y el General —que ve lejos— sabrá si lo hemos merecido.» (estampa el sello «INFORME ENTREGADO» sobre el sobre) "
                                  "«Escuadrón SONAR: misión cumplida. Cambio y fuera.»"),
          dialogo("SARGENTO BRAVO", "«¡Señor, sí, señor!»"),
          Spacer(1, 1)]
    S += [P("<b>Tarjeta final:</b> fondo negro. «MISIÓN: CERO PUNTO DOS». Debajo: «Los números no se pierden. Esperan a que alguien los explique.» "
            "Créditos humorísticos (3 s): «Ninguna décima fue maltratada durante el rodaje. Ningún cable suelto fue ascendido.»", small)]

    # ---------------------------------------------------------------- 3. Producción
    S += [PageBreak(), P("3 · Plan de producción", H1)]
    S += [P("Cómo grabar: las tomas, la ropa y todo lo demás", H2)]

    S += [P("3.1 · Reglas de oro", H2)]
    S += [P("• <b>El audio manda.</b> Un video con buena voz y mala imagen se perdona; al revés, no.<br/>"
            "• <b>Los dos hablan.</b> La rúbrica pide que participen activamente los dos desarrolladores.<br/>"
            "• <b>Todo lo que se explique debe verse.</b> Cada frase técnica se dice con la pieza o la pantalla en cuadro.<br/>"
            "• <b>Nada falso.</b> No nombrar piezas que no estén montadas ni funciones que no se vean funcionar.<br/>"
            "• <b>Grabar suelto, montar después.</b> Tomas cortas, con 3 segundos de silencio antes y después.")]

    S += [P("3.2 · Cámara y tomas", H2)]
    S += [tabla([["Concepto", "Cómo"],
                 ["Formato", "Celular <b>horizontal</b>, 1080p a 30 fps, trípode (o apoyar el celular en libros). Bloquear enfoque y exposición (mantener pulsado sobre la pantalla)."],
                 ["Encuadre", "Regla de tercios; Bravo ligeramente a un lado, el montaje al otro. Ojos a la altura del lente."],
                 ["Plano general", "Muestra el conjunto: mesa, montaje, hoja y celular. Una vez por escena."],
                 ["Plano medio", "De cintura para arriba: para hablar. La mayor parte de las líneas."],
                 ["Plano detalle (macro)", "Piezas, láser sobre la esquina, servos, el dedo en STOP. Grabar 10 s de cada pieza aunque no se use."],
                 ["Cenital (desde arriba)", "Para el tablero y la hoja: el celular boca abajo sobre una caja, o la cámara en una silla invertida."],
                 ["Contrapicado (desde abajo)", "Solo en la apertura y el cierre, para dar autoridad a Alfa."],
                 ["Cámara lenta", "120 o 240 fps si el celular lo permite, para los servos moviéndose y el láser apagándose."],
                 ["Pantalla del celular", "Usar la <b>grabación de pantalla</b> del propio celular; la voz se graba aparte y se pone encima."]],
                [38, 136])]

    S += [P("3.3 · Lista de tomas", H2)]
    S += [tabla([["#", "Toma", "Quién", "Plano", "Dur."],
                 ["1", "Sobre sellado: la mano rompe el sello (frío)", "Sebas", "Detalle + estática", "0:15"],
                 ["2", "Acto I: la orden a cámara", "Sebas", "Medio, contrapicado leve", "0:40"],
                 ["3", "Entrada de Bravo y caída de la tela", "Bravo", "Medio a general", "0:10"],
                 ["4", "Escena 1: tablero cenital + Bravo con la regla", "Bravo", "Cenital + medio", "0:30"],
                 ["5", "Escena 2: pieza por pieza con rótulos", "Bravo", "Detalles + medio", "0:45"],
                 ["6", "Escena 3: láser en las 4 esquinas + pantalla de calibración + disparo", "Bravo", "Detalle + pantalla + general", "1:00"],
                 ["7", "Escena 4: servos suaves + STOP", "Bravo", "Cámara lenta + detalle", "0:40"],
                 ["8", "Escena 5: grabación de pantalla de la app + hoja de bolsillo", "Bravo", "Pantalla + detalle", "1:00"],
                 ["9", "Escena 6: test de 5 posiciones", "Bravo", "General fijo + detalles", "0:35"],
                 ["10", "Acto III: diálogo final y estampado del sello", "Los dos", "Medio de los dos + detalle del sello", "0:45"],
                 ["11", "Tarjeta final", "—", "Cartón o texto en la edición", "0:05"],
                 ["12", "Planos de recurso («B-roll»): servos, láser, pilas, hoja", "—", "Detalles de 10 s", "extra"]],
                [8, 84, 18, 48, 16])]
    S += [Spacer(1, 2), P("<b>Orden de rodaje:</b> se graba por lugar y por luz, no por orden del guion: primero las tomas de la mesa (3 a 9), luego Alfa (1, 2, 10). "
                          "Cada toma, mínimo dos veces; la segunda siempre sale mejor.", small)]

    S += [P("3.4 · Vestuario y personajes", H2)]
    S += [tabla([["", "Capitán ALFA (Sebas)", "Sargento BRAVO ([Compañero])"],
                 ["Prenda base", "Camiseta o chaqueta <b>verde oliva</b> o negra; pantalón oscuro.", "Camisa o chaqueta de <b>campo</b> (arena, caqui, oliva); pantalón oscuro."],
                 ["Cabeza", "Gorra o boina oscura, bien puesta.", "Gorra echada hacia atrás o banda en la frente."],
                 ["Insignia", "Tres rayas de cinta amarilla en el brazo; cinta de enmascarar con «ALFA» escrito con marcador.", "Dos rayas de cinta; cinta con «BRAVO» en el brazo."],
                 ["Detalles", "Linterna colgada, reloj visible, cinturón.", "Una «mancha de campaña» de carboncillo o maquillaje en la mejilla; cuaderno de campo en el bolsillo."],
                 ["Actitud", "Voz baja, pausada, sin gritar. Una sola ceja levantada en el humor.", "Voz clara y firme; cuando explica, <b>sonríe poco y habla con seguridad</b>. Es el experto del escuadrón."]],
                [24, 75, 75])]
    S += [Spacer(1, 3), caja("IMPORTANTE", "No usar uniformes ni insignias reales de ningún ejército, ni réplicas de armas. Es un disfraz de <i>cuento de guerra</i>: ropa civil estilo campo, "
                                          "cintas y cartón. El humor es el escuadrón, no las fuerzas armadas.", fondo=colors.HexColor("#FBE9E7"), borde=ROJO)]

    S += [P("3.5 · Locación, decorado y utilería", H2)]
    S += [P("• <b>Locación:</b> una mesa contra una pared lisa, lejos de ventanas con contraluz fuerte. Sin carteles ni objetos que distraigan.<br/>"
            "• <b>Decorado:</b> tela o sábana <b>verde oliva</b> (o gris) sobre la mesa; una malla o tela rasgada como «camuflaje»; mapa o cartulina con una cruz roja como «plano de operaciones».<br/>"
            "• <b>Utilería:</b> el <b>sobre sellado</b> (sobre manila, sello rojo hecho con cera o marcador, texto «ORDEN DEL GENERAL · CONFIDENCIAL» y otro sello «INFORME ENTREGADO»); "
            "linterna; reloj; cuaderno de campo; un celular como «radio de campaña» con cinta; binoculares o tubo de cartón; las cartulinas de título; la hoja impresa y las plantillas de bolsillo.<br/>"
            "• <b>El montaje</b> debe estar limpio: cables amarrados, tablero sin polvo. Ayuda a la nota de estética, aunque sea con cinta.")]

    S += [P("3.6 · Luz y color", H2)]
    S += [P("• <b>Apertura y Acto I:</b> penumbra con una sola luz cálida de lado (lámpara o linterna); sombras largas.<br/>"
            "• <b>Informe técnico:</b> más luz, pero siempre suave y lateral; que el láser se vea, así que atenuar la luz general en las tomas del láser.<br/>"
            "• <b>Acto III:</b> luz cálida de «amanecer» (lámpara amarilla o luz de ventana por un costado).<br/>"
            "• <b>Color en la edición:</b> verdes y arenas desaturados, contraste suave y viñeta ligera; el rojo del láser debe resaltar.")]

    S += [P("3.7 · Sonido y música", H2)]
    S += [P("• Grabar la voz con el celular a 30 cm de la boca, en un cuarto sin eco (cortinas, colchón detrás). Si hay audífonos con micrófono, mejor.<br/>"
            "• Grabar <b>10 segundos de silencio</b> del lugar («tono de sala») para limpiar el ruido.<br/>"
            "• <b>Música:</b> marcha instrumental o épica suave de bibliotecas <b>libres de derechos</b> (YouTube Audio Library, Pixabay). Solo en apertura y cierre; en el informe, casi silencio.<br/>"
            "• <b>Efectos:</b> estática de radio, pitido de comunicación, redoble corto y el golpe de sello; volumen bajo, sin tapar la voz.<br/>"
            "• <b>Voz del General:</b> Sebas con la voz más grave y filtro tipo radio (el editor tiene el efecto «teléfono» o «radio»).")]

    S += [P("3.8 · Texto en pantalla y edición", H2)]
    S += [P("• <b>Tipografía:</b> máquina de escribir o estarcido (<i>Special Elite</i>, <i>Stencil</i>, <i>Courier</i>).<br/>"
            "• <b>Rótulos:</b> cada pieza se nombra en pantalla al aparecer (Cerebro, Torres, Ojo…), con la palabra real debajo (ESP32, servo, láser).<br/>"
            "• <b>Títulos de acto:</b> cartulinas escritas a mano, en plano fijo de 2 segundos.<br/>"
            "• <b>Transiciones:</b> corte seco y fundido a negro; el único efecto especial es el sello. Nada de transiciones llamativas.<br/>"
            "• <b>Ritmo:</b> ningún plano de más de 8 segundos sin cambiar de imagen. Cortar las pausas y las muletillas.<br/>"
            "• <b>Programas:</b> CapCut (celular) o DaVinci Resolve (PC, gratis). <b>Exportar</b> en MP4 1080p, y que dure <b>6:00 o menos</b>.<br/>"
            "• <b>Archivo:</b> «Mision-Cero-Punto-Dos_SONAR.mp4».")]

    S += [P("3.9 · Seguridad y legalidad", H2)]
    S += [caja("EL LÁSER", "<b>Nunca apuntar el láser a los ojos ni a la lente de la cámara</b> (puede dañar el sensor del celular). Siempre sobre la hoja o el tablero. "
                           "Nadie mira directo al haz. Grabar con luz baja pero sin tapar la mirada del que opera.", fondo=colors.HexColor("#FBE9E7"), borde=ROJO)]
    S += [Spacer(1, 3), P("• Música y efectos solo de fuentes libres de derechos. • No usar símbolos, escudos ni uniformes reales. • Nombrar a «el General» con respeto: es un homenaje, no una burla.")]

    S += [P("3.10 · Lista del día de rodaje", H2)]
    S += [tabla([["Antes de grabar", "Durante", "Después"],
                 ["[  ] Pilas nuevas y firmware 0.2.0 cargado<br/>[  ] Calibración guardada y TEST probado dos veces<br/>[  ] Celular cargado y con espacio<br/>[  ] Utilería y vestuario listos<br/>[  ] Mesa y montaje limpios<br/>[  ] Guion impreso y repasado",
                  "[  ] Luz de frente o lateral, nunca contraluz<br/>[  ] Audio probado: grabar 5 s y escuchar<br/>[  ] Cada toma, 2 veces<br/>[  ] 3 s de silencio antes y después<br/>[  ] Grabar el tono de sala y los planos de recurso<br/>[  ] Agua para la voz",
                  "[  ] Copiar todo a la PC/Drive el mismo día<br/>[  ] Montar en el orden del guion<br/>[  ] Subtítulos y rótulos<br/>[  ] Revisar el audio con audífonos<br/>[  ] Verificar duración máxima 6:00<br/>[  ] Entregar a tiempo"]],
                [58, 58, 58])]

    S += [PageBreak(), P("4 · Hoja de repaso del Sargento Bravo", H1)]
    S += [P("Si el General pregunta de nuevo, estas son las respuestas cortas.", small), Spacer(1, 3)]
    S += [tabla([["Pregunta", "Respuesta corta"],
                 ["¿Qué hace el ESP32?", "Recibe (x,y) por Bluetooth, calcula los ángulos de dos servos, los mueve y enciende el láser con un pitido."],
                 ["¿Por qué los servos van aparte?", "Al arrancar consumen mucha corriente; si salieran del ESP32 lo reiniciarían. Van con 6 V de pilas y GND común."],
                 ["¿Para qué el capacitor?", "Amortigua el pico de corriente del arranque de los servos."],
                 ["¿Cómo sabe adónde apuntar?", "Se calibra apuntando a las 4 esquinas; el módulo calcula las 400 casillas con una homografía."],
                 ["¿Qué es el punto de control?", "El centro (11,11): se compara lo medido con lo calculado; el error dice qué tan buena es la calibración."],
                 ["¿Por qué el último tramo es lento y subiendo?", "Para eliminar la holgura de los engranes y que siempre llegue por el mismo lado."],
                 ["¿Es seguro el láser?", "Nunca está encendido mientras se mueven los servos; STOP lo apaga al instante; se apaga solo si se olvida."],
                 ["¿Qué manda la app?", "Un texto (x,y): primero x, luego y."],
                 ["¿Qué es el test de 5 posiciones?", "Las cuatro esquinas y el centro, en el propio sistema tablero-estación."],
                 ["¿Qué es original?", "El firmware en C++ con pruebas automáticas, la app propia y el protocolo propio; el historial de commits lo demuestra."],
                 ["¿Y si el rival usa otra app?", "Mientras mande (x,y) por Bluetooth, el módulo la acepta, incluso sin salto de línea."],
                 ["¿Qué mejorarían?", "La estética (cableado y acabado) y registrar más puntos de calibración desde la app."]],
                [58, 116])]
    S += [Spacer(1, 10), P("<i>«Hay batallas que no se ganan con la fuerza: se ganan explicándolas.»</i>", ParagraphStyle("f", parent=lyric, alignment=TA_CENTER, textColor=OLIVA, fontSize=11))]

    doc.build(S, onFirstPage=portada, onLaterPages=interior)


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "docs", "impresos", "GUION-Mision-Cero-Punto-Dos.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build(out)
    print("OK", out)
