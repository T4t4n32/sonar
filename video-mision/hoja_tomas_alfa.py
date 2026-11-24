"""Hoja de tomas del Capitán ALFA (Sebas): qué decir, cómo vestir y cómo grabar. Uso: uv run --with reportlab python hoja_tomas_alfa.py"""
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
H2 = ParagraphStyle("h2", parent=base, fontName="Courier-Bold", fontSize=12.5, leading=16, textColor=OLIVA, spaceBefore=9, spaceAfter=3)
big = ParagraphStyle("big", parent=base, fontName="Helvetica-Bold", fontSize=14.5, leading=21)
nota = ParagraphStyle("n", parent=base, fontSize=9, leading=12.4, textColor=colors.HexColor("#444444"))


def P(t, s=base):
    return Paragraph(t, s)


def caja(titulo, cuerpo, borde=OLIVA, fondo=CLARO):
    t = Table([[P(f"<b>{titulo}</b><br/>{cuerpo}", nota)]], colWidths=[176 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fondo), ("BOX", (0, 0), (-1, -1), 0.8, borde),
                           ("LEFTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def linea(rol, texto):
    t = Table([[P(f"<b>{rol}</b>", ParagraphStyle("r", parent=nota, textColor=ROJO, fontName="Helvetica-Bold")), P(texto, big)]], colWidths=[26 * mm, 150 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBEFORE", (1, 0), (1, 0), 1.8, ORO), ("LEFTPADDING", (1, 0), (1, 0), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def tabla(filas, anchos):
    d = [[P(c, ParagraphStyle("c", parent=nota, fontName="Helvetica-Bold" if i == 0 else "Helvetica")) for c in f] for i, f in enumerate(filas)]
    t = Table(d, colWidths=[a * mm for a in anchos])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA38A")), ("BACKGROUND", (0, 0), (-1, 0), CLARO), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def pie(c, doc):
    w, h = letter
    c.saveState()
    c.setFillColor(OLIVA)
    c.rect(0, h - 10 * mm, w, 10 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#EFE9D8"))
    c.setFont("Courier-Bold", 8.5)
    c.drawString(18 * mm, h - 6.6 * mm, "MISIÓN: CERO PUNTO DOS  ·  HOJA DE TOMAS  ·  CAPITÁN ALFA")
    c.drawRightString(w - 18 * mm, h - 6.6 * mm, f"pág. {doc.page}")
    c.restoreState()


def build(path):
    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=17 * mm, rightMargin=17 * mm, topMargin=16 * mm, bottomMargin=14 * mm,
                            title="Hoja de tomas - Capitán ALFA", author="Escuadrón SONAR")
    S = [P("Capitán ALFA · tus 3 tomas", H1),
         P("Grabas <b>tres cosas</b>: la voz del General (solo audio), la <b>orden</b> (a cámara) y el <b>regreso</b> (con tu compañero). Todo lo demás lo arma el programa. "
           "Cada toma, <b>mínimo dos veces</b>; si te trabas, vuelves a empezar la frase, no el video.", base),
         Spacer(1, 4),
         tabla([["Toma", "Qué es", "Dura", "Archivo"],
                ["A", "Voz del General (solo audio, se pone sobre el sobre)", "~12 s", "<b>voz/P1_sebas.ogg</b> (ya está)"],
                ["B", "ACTO I · La orden (a cámara, o solo la voz)", "~40 s", "<b>tomas/01-orden.mp4</b> o <b>voz/01-orden.m4a</b>"],
                ["C", "ACTO III · El regreso (con tu compañero)", "~45 s", "<b>tomas/08-regreso.mp4</b>"]],
               [14, 100, 18, 44]),
         P("Vestuario del Capitán ALFA", H2),
         tabla([["Prenda", "Qué ponerte"],
                ["Base", "Camiseta, camisa o chaqueta <b>verde oliva</b> (o negra). Pantalón oscuro. Combina con los clips: verdes y arena, nada brillante."],
                ["Cabeza", "Gorra o boina <b>oscura</b>, bien puesta, sin logos visibles."],
                ["Rango (hecho en casa)", "<b>Tres rayas de cinta amarilla</b> en el brazo y una cinta de enmascarar con <b>«ALFA»</b> escrito con marcador."],
                ["Detalles", "Reloj visible, una linterna colgada del cinturón o en la mano, cinturón."],
                ["Actitud", "Voz baja y pausada, sin gritar. Mira a la lente. Una ceja levantada en el humor. Nadie se ríe en cámara."],
                ["NO", "Nada de uniformes ni insignias reales, ni réplicas de armas, ni logos de marcas. Es un cuento de guerra: ropa civil estilo campo."]],
               [32, 144]),
         P("Cómo montar tu toma", H2),
         P("• <b>Celular horizontal</b>, en trípode o apoyado en libros, a la altura de tus ojos, plano de cintura para arriba (un poco desde abajo, para dar autoridad).<br/>"
           "• <b>Fondo:</b> pared lisa oscura y la mesa con la <b>tela verde oliva</b> delante; encima el <b>sobre manila</b> (con un sello de cera o un círculo rojo dibujado).<br/>"
           "• <b>Luz:</b> casi a oscuras, con <b>una sola luz cálida de lado</b> (lámpara o la linterna); que se vea tu cara a medias.<br/>"
           "• <b>Audio:</b> cuarto sin eco (cortinas, colchón detrás), el celular a 30 cm de la boca. Graba 5 s y escúchalos antes de empezar.<br/>"
           "• <b>Ayuda:</b> abre este PDF en el portátil, <b>justo debajo o al lado de la cámara</b>, y léelo mirando casi a la lente. Dilo con tus palabras, no de memoria.")]

    S += [PageBreak()]
    S += [P("TOMA A · La voz del General (solo audio)", H2),
          caja("Cómo", "Grábala <b>como nota de voz</b> del celular. Voz grave, baja, lenta, a unos 20 cm. Deja <b>2 segundos de silencio al principio y al final</b>. "
                       "Se pone sobre el clip del sobre con filtro de radio, así que no necesitas efecto. Guárdala como <b>voz/00-general</b>."),
          Spacer(1, 3),
          linea("EL GENERAL", "«Escuadrón SONAR. <i>(pausa)</i><br/>Hay números que no se pierden: <b>esperan</b>. <i>(pausa)</i><br/>Dos décimas quedaron en el campo de la Estética. <i>(pausa)</i><br/>"
                              "El Cinco no se negocia. <i>(pausa)</i><br/>Tienen un informe que dar.»")]

    S += [P("TOMA B · Acto I: La orden (a cámara, ~40 s)", H2),
          caja("Escena", "Plano medio, luz de lado. Tienes el <b>sobre abierto</b> en la mano o sobre la mesa. Empiezas mirando el sobre, y levantas la vista en «Escuadrón SONAR». "
                         "Al final, <b>giras la cabeza hacia tu compañero</b> y él entra a cuadro y saluda (se puede grabar aparte: entra, saludo, «A la orden…»)."),
          Spacer(1, 3),
          linea("CAPITÁN ALFA", "«Escuadrón SONAR, aquí el <b>Capitán Alfa</b>. <i>(pausa)</i>"),
          linea("", "Hace unos días libramos la batalla del corte final. Salimos con la frente en alto… y <b>cuatro coma ocho</b> en el morral. <i>(pausa)</i>"),
          linea("", "Dos décimas se quedaron atrás, caídas en la <b>Trinchera de la Estética</b>. <i>(pausa)</i>"),
          linea("", "El General —que ve lejos y pregunta bien— dictó una sola orden: <b>explicar la campaña, completa, ante cámara.</b> <i>(pausa)</i>"),
          linea("", "Porque este escuadrón no persigue un número. Persigue <b>el Cinco Sagrado</b>. <i>(pausa)</i>"),
          linea("", "No pido venganza: pido un informe. <i>(mirando hacia el lado)</i> Sargento Bravo… <b>el frente es suyo.</b>»"),
          Spacer(1, 3),
          caja("Si te trabas", "No pares: repite solo la frase donde te trabaste y sigue. El programa corta; tú dale dos pasadas completas.", borde=ROJO, fondo=colors.HexColor("#FBE9E7"))]

    S += [PageBreak(), P("TOMA C · Acto III: El regreso (con [Compañero], ~45 s)", H2),
          caja("Escena", "Plano medio de los dos, de frente, <b>luz más cálida</b> (lámpara amarilla o una ventana por un costado: es el amanecer). Tú sostienes el sobre. "
                         "Al terminar, <b>los dos saludan</b> y se quedan quietos 3 segundos. <i>(Si tienes un sello de goma, estampa «INFORME ENTREGADO»; si no, no hace falta: el sello sale en la tarjeta final.)</i>"),
          Spacer(1, 3),
          linea("ALFA", "«Sargento, ¿con cuánto volvemos del frente?»"),
          linea("BRAVO", "«Con cuatro coma ocho, Capitán… y con el informe completo.»"),
          linea("ALFA", "«Cuatro coma ocho… y dos esquirlas por recoger.»"),
          linea("BRAVO", "«Cero coma dos, Capitán. Lo que separa a este escuadrón del Cinco Sagrado.»"),
          linea("ALFA", "«El Cinco no se toma. <b>Se merece.</b> Y el General —que ve lejos— sabrá si lo hemos merecido. <i>(mira a cámara)</i> "
                        "Escuadrón SONAR: <b>misión cumplida.</b> Cambio y fuera.»"),
          linea("BRAVO", "«¡Señor, sí, señor!»"),
          Spacer(1, 4),
          caja("Después de grabar", "Pasa los archivos con estos nombres a la carpeta <b>video-mision/tomas/</b> (<b>01-orden</b> y <b>08-regreso</b>) y la nota de voz a <b>video-mision/voz/</b> (<b>00-general</b>). "
                                   "Dime «listo» y lo monto.")]
    doc.build(S, onFirstPage=pie, onLaterPages=pie)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HOJA-TOMAS-CAPITAN-ALFA.pdf")
    build(out)
    print("OK", out)
