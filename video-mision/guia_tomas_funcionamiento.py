"""Guía paso a paso para grabar las tomas de FUNCIONAMIENTO (evidencia real). Uso: uv run --with reportlab python guia_tomas_funcionamiento.py"""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OLIVA = colors.HexColor("#3E4A2B")
CLARO = colors.HexColor("#E7EAD9")
ORO = colors.HexColor("#B8892B")
ROJO = colors.HexColor("#8C2B22")
base = ParagraphStyle("b", fontName="Helvetica", fontSize=10, leading=14)
H1 = ParagraphStyle("h1", parent=base, fontName="Courier-Bold", fontSize=17, leading=21, textColor=OLIVA, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=base, fontName="Courier-Bold", fontSize=12, leading=15, textColor=OLIVA, spaceBefore=8, spaceAfter=3)
small = ParagraphStyle("s", parent=base, fontSize=9, leading=12.4, textColor=colors.HexColor("#444444"))
dec = ParagraphStyle("d", parent=base, fontName="Helvetica-Bold", fontSize=13, leading=19)


def P(t, s=base):
    return Paragraph(t, s)


def caja(titulo, cuerpo, borde=OLIVA, fondo=CLARO):
    t = Table([[P(f"<b>{titulo}</b><br/>{cuerpo}", small)]], colWidths=[176 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fondo), ("BOX", (0, 0), (-1, -1), 0.8, borde), ("LEFTPADDING", (0, 0), (-1, -1), 7),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def toma(cod, titulo, archivo, dur, pasos, ojo=None):
    cab = Table([[P(f"<font color='white'><b>{cod}</b></font>", ParagraphStyle("c", parent=base, fontName="Courier-Bold", fontSize=11, alignment=1)),
                  P(f"<b>{titulo}</b>", ParagraphStyle("t", parent=base, fontName="Courier-Bold", fontSize=11, textColor=OLIVA)),
                  P(f"{dur} · <b>{archivo}</b>", ParagraphStyle("r", parent=small, alignment=2))]], colWidths=[13 * mm, 87 * mm, 76 * mm])
    cab.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), OLIVA), ("BACKGROUND", (1, 0), (2, 0), CLARO), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    cuerpo = "<br/>".join(f"{i + 1}. {p}" for i, p in enumerate(pasos))
    out = [cab, Spacer(1, 2), P(cuerpo, base)]
    if ojo:
        out += [Spacer(1, 2), caja("OJO", ojo, borde=ROJO, fondo=colors.HexColor("#FBE9E7"))]
    return KeepTogether(out + [Spacer(1, 5)])


def pie(c, doc):
    w, h = letter
    c.saveState()
    c.setFillColor(OLIVA)
    c.rect(0, h - 10 * mm, w, 10 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#EFE9D8"))
    c.setFont("Courier-Bold", 8.5)
    c.drawString(18 * mm, h - 6.6 * mm, "MISIÓN: CERO PUNTO DOS  ·  TOMAS DE FUNCIONAMIENTO")
    c.drawRightString(w - 18 * mm, h - 6.6 * mm, f"pág. {doc.page}")
    c.restoreState()


def build(path):
    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=17 * mm, rightMargin=17 * mm, topMargin=16 * mm, bottomMargin=14 * mm,
                            title="Tomas de funcionamiento", author="Escuadrón SONAR")
    S = [P("Tomas de funcionamiento · paso a paso", H1),
         P("Son las <b>pruebas con evidencia real</b>: lo que demuestra que el sistema funciona. Con ellas el video deja de usar fotos fijas y capturas de la app y pasa a mostrar el "
           "montaje de verdad. <b>Entre las 7 tomas son unos 20 minutos de grabación.</b> Si solo hay tiempo para tres, graba <b>F1, F2 y F3</b>.", base),
         Spacer(1, 4),
         P("Antes de empezar (5 minutos)", H2),
         P("[  ] <b>Pilas nuevas</b> y el ESP32 con el firmware 0.2.0 cargado (<b>PING</b> responde <b>PONG SONAR-A 0.2.0</b>).<br/>"
           "[  ] <b>Calibración guardada</b> con la hoja impresa pegada firme (4 esquinas + centro) y un <b>TEST</b> probado dos veces seguidas antes de grabar.<br/>"
           "[  ] La hoja <b>plana y bien iluminada solo por la luz de la habitación</b>: poca luz para que el láser rojo se vea, pero que se distinga la hoja.<br/>"
           "[  ] Celular con carga y espacio. <b>Dos personas</b>: una opera (presiona en la app) y otra graba. Un trípode o libros para apoyar el celular que graba.<br/>"
           "[  ] Los celulares en <b>horizontal</b>, y todo con <b>tres segundos de silencio</b> antes y después."),
         caja("SEGURIDAD", "El láser <b>nunca apunta a ojos ni a la lente</b>. Quien graba se pone al lado o detrás del montaje, no frente a la salida del haz.", borde=ROJO, fondo=colors.HexColor("#FBE9E7")),
         Spacer(1, 4)]

    S += [toma("F1", "La app funcionando (grabación de pantalla)", "evidencia/pantalla-app.mp4", "45–60 s",
               ["En el celular con la app, activa la <b>grabación de pantalla</b> (barra de arriba → «Grabar pantalla»; en Xiaomi, Seguridad → Grabadora de pantalla).",
                "<b>Enlace</b>: se ve la conexión con <b>SONAR-A</b> (estado «Conectado»).",
                "<b>Batalla</b>: elige una casilla, por ejemplo (10, 15), y pulsa <b>DISPARAR</b>.",
                "Sale <b>«¿Le dio?»</b>: responde <b>SÍ</b> sobre un barco de la plantilla en juego. Se ve el barco hundido y la posición.",
                "Pestaña <b>Partida</b>: se ven los botones de <b>Plantilla 1 a 5</b>. Toca la 2 y se ve que empieza partida nueva."],
               "Que sea una conexión real a SONAR-A, no el «modo simulado». Si dice SONAR-SIM, no sirve como evidencia del enlace."),
          toma("F2", "El láser cae en las 5 posiciones (el TEST)", "tomas/07-prueba.mp4", "40–50 s",
               ["Cámara <b>fija, a unos 40 cm y algo de lado (45°)</b> de la hoja, que se vea la hoja completa y, al fondo, el montaje de los servos.",
                "<b>Luces bajas.</b> Empieza a grabar y espera 3 segundos.",
                "La otra persona pulsa <b>TEST</b> en la app. El láser recorre las <b>4 esquinas y el centro</b>.",
                "Quien opera dice en voz alta, con tono firme: «Cinco posiciones: las cuatro esquinas y el centro… una… dos… tres… cuatro… cinco. El Ojo estuvo donde debía. Prueba superada.»",
                "Deja el plano 3 segundos más y corta."],
               "Repite el TEST dos o tres veces y quédate con el mejor. Si una posición falla, no cortes: di «se corrige recalibrando» y repite. Es más honesto y explica mejor."),
          toma("F3", "Los servos de cerca (el pulso sereno)", "evidencia/maqueta.mp4", "15–20 s",
               ["Celular a <b>20–30 cm</b> de los servos y el láser, plano fijo y bien enfocado (toca la pantalla para fijar el enfoque).",
                "Opera <b>JOG</b> o dispara de la casilla (1,1) a la (20,20) y de vuelta: se ven los <b>dos servos moviéndose a la vez, suaves</b>.",
                "Graba el recorrido completo, sin cortar."])]

    S += [PageBreak()]
    S += [toma("F4", "STOP: el láser se apaga al instante", "evidencia/stop.mp4", "10–15 s",
               ["Plano de la hoja con el láser encendido (después de un disparo el láser queda encendido).",
                "Se ve el celular en cuadro (o en un segundo plano) y alguien pulsa <b>STOP</b>: el punto rojo <b>desaparece</b>.",
                "Si puedes, un plano de la pantalla con el botón STOP en rojo."]),
          toma("F5", "El sonido del disparo", "evidencia/pitido.mp4", "5–10 s",
               ["Celular cerca del zumbador (o del celular que suena), plano del montaje.", "Dispara una casilla: se oye el <b>pitido</b> y se enciende el láser."],
               "Si el zumbador no está conectado, <b>no grabes esta toma ni lo nombres en el video</b>: la rúbrica pide «un sonido con cada disparo», así que conecta el zumbador (+ a GPIO 21, − a GND) si puedes."),
          toma("F6", "La calibración real", "evidencia/calibracion.mp4", "20–30 s",
               ["Plano de la hoja con el láser en una esquina y, al lado, el celular con la pantalla «Calibrar apuntado».",
                "Mueve el láser con la cruceta hasta la esquina y pulsa «Esta es la esquina (1,1)». Repite rápido con otra esquina.",
                "Termina con <b>Calcular</b>: se ve el error de control en grados."]),
          toma("F7", "La plantilla pintada y el barco hundido", "evidencia/plantilla.mp4", "20–25 s",
               ["Plano cenital (desde arriba) de la <b>plantilla pintada</b> sobre la mesa. Muestra el número de plantilla.",
                "Dispara a una casilla de un barco: el láser cae sobre el barco pintado.",
                "Corte al celular: la app dice que el barco se hundió y <b>dónde estaba</b>."]),
          toma("F8", "El regreso: los dos en cámara", "tomas/08-regreso.mp4", "~45 s",
               ["Sebas y Juan José frente al montaje, luz más cálida (amanecer). Diálogo de la hoja de tomas de Alfa.",
                "Al terminar, los dos saludan y se quedan quietos 3 segundos."])]

    S += [toma("F9", "Foto del tablero con regla (para mostrar los 5 cm)", "evidencia/tablero.jpg", "1 foto",
               ["Foto de <b>lado</b>, a la altura de la mesa: el <b>tablero de 30×30 cm elevado 5 cm</b> sobre la base, con una <b>regla</b> midiendo los 5 cm contra la mesa.",
                "Otra foto <b>de arriba</b> con la regla de 30 cm sobre el borde (opcional)."],
               "Mientras no exista esta foto, el video rotula esa imagen como «Estación de ataque» y no afirma las medidas del tablero.")]
    S += [P("Cómo me los pasas", H2),
          P("Guarda los archivos con <b>estos nombres</b> en <b>video-mision/tomas/</b> (las que dicen «tomas/») o <b>video-mision/evidencia/</b> (las que dicen «evidencia/»), y dime <b>«listo»</b>. "
            "El montaje reemplaza solo las fotos fijas por tus videos reales (por ejemplo, <b>evidencia/maqueta.mp4</b> sustituye la foto de los servos) y vuelve a armar el video completo."),
          Spacer(1, 4),
          caja("Si te quedas sin tiempo", "Mínimo viable: <b>F1</b> (app), <b>F2</b> (TEST, que es lo que más pesa en la nota) y <b>F8</b> (el regreso). Con eso el video queda completo y lo demás se cubre con las fotos y capturas que ya están montadas.")]
    doc.build(S, onFirstPage=pie, onLaterPages=pie)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUIA-TOMAS-FUNCIONAMIENTO.pdf")
    build(out)
    print("OK", out)
