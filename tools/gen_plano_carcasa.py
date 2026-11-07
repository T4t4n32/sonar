#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera PLANO_CARCASA_SONAR.pdf — Plano 1:1 de carcasa y soporte.
ACADEMICO (UAO) / ejercer poder sobre código en PDF
"""
import math
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "PLANO_CARCASA_SONAR.pdf")

def dim_text(c, x, y, s, size=6, angle=0, color=colors.black):
    c.saveState(); c.translate(x, y); c.rotate(angle)
    c.setFont('Helvetica', size); c.setFillColor(color)
    c.drawCentredString(0, 0, s); c.restoreState()

def line(c, x1, y1, x2, y2, w=0.6, col=colors.black):
    c.setStrokeColor(col); c.setLineWidth(w); c.line(x1, y1, x2, y2)

def arrow_dim_h(c, x1, x2, y, text, size=6):
    line(c, x1, y, x2, y, 0.4)
    for x in (x1, x2):
        line(c, x, y-1.5*mm, x, y+1.5*mm, 0.4)
        c.setFont('Helvetica', size); c.setFillColor(colors.black)
        c.drawCentredString((x1+x2)/2, y+2*mm, text)

def arrow_dim_v(c, y1, y2, x, text, size=6):
    line(c, x, y1, x, y2, 0.4)
    for y in (y1, y2):
        line(c, x-1.5*mm, y, x+1.5*mm, y, 0.4)
    c.saveState(); c.translate(x+2*mm, (y1+y2)/2); c.rotate(90)
    c.setFont('Helvetica', size); c.drawCentredString(0, 0, text); c.restoreState()

def header_footer(c, page, total, W, H, title):
    c.setFont('Helvetica-Bold', 16)
    c.drawString(15*mm, H-13*mm, 'SONAR — ' + title)
    c.setFont('Helvetica', 8)
    c.drawString(15*mm, H-17*mm, 'Fundamentos de Mecatrónica (UAO)  •  ESP32 WROOM-32  •  Torreta Pan-Tilt  •  Láser KY-008')
    c.setFont('Helvetica', 6.5)
    c.drawString(15*mm, H-21*mm, 'Fecha: 2026-11-04  •  Autores: Sebastián Sánchez Chacón / Jader Andrés Astaiza Ocampo  •  Todas las cotas en mm. Origen (0,0): esquina posterior-izquierda del tablero (1,1). X→derecha, Y→frente, Z↑')
    line(c, 15*mm, H-22*mm, W-15*mm, H-22*mm, 0.4)
    c.setFont('Helvetica', 6)
    c.drawRightString(W-15*mm, 10*mm, f'Página {page} de {total}  •  Escala indicada en cada vista')
    c.setFont('Helvetica-Oblique', 6)
    c.drawString(15*mm, 10*mm, 'Documento de fabricación — verificar tolerancias antes de cortar/imprimir. No alimentar servos desde el pin 5V del ESP32.')

# -------------------------------------------------
# Cotas del proyecto (config.h)
GRID_N = 20
CELL_MM = 10.0
STATION_X, STATION_Y = 100.0, -65.0
TILT_H = 180.0
PAN_LIMIT = 57.0
TILT_MIN, TILT_MAX = 30.0, 72.0

def build():
    W, H = landscape(A3)  # 420 x 297 mm
    c = canvas.Canvas(OUT, pagesize=landscape(A3))
    c.setTitle('SONAR — Plano de Carcasa y Soporte (1:1)')
    c.setAuthor('Sebastián Sánchez Chacón / Jader Andrés Astaiza Ocampo')
    pages = 6
    # =============== PAGINA 1: Vista en planta (top) ===============
    header_footer(c, 1, pages, W, H, 'Vista en Planta — Tablero + Estación Pan-Tilt (Escala 1:1)')
    # Vista central: tablero 200x200 a 1:1 si cabe en A3 landscape (420mm wide). Usamos 200x200 + base trasera.
    # Origen en (120mm, 60mm) en página. Escala 1mm=1mm => s=1
    s = 1.0 * mm
    ox, oy = 60*mm, 55*mm  # origen X=0,Y=0 del tablero
    # Tablero
    for (x1,y1,x2,y2,w,col) in [
        (ox,oy, ox+200*s,oy, 0.9, colors.black),
        (ox,oy, ox,oy+200*s, 0.9, colors.black),
        (ox+200*s,oy, ox+200*s,oy+200*s, 0.9, colors.black),
        (ox,oy+200*s, ox+200*s,oy+200*s, 0.9, colors.black),
    ]: line(c,x1,y1,x2,y2,w,col)
    # Rejilla fina
    for i in range(21):
        line(c, ox+i*CELL_MM*s, oy, ox+i*CELL_MM*s, oy+200*s, 0.18, colors.HexColor('#BBBBBB'))
        line(c, ox, oy+i*CELL_MM*s, ox+200*s, oy+i*CELL_MM*s, 0.18, colors.HexColor('#BBBBBB'))
    # Etiquetas filas/columnas
    c.setFont('Helvetica', 4.5); c.setFillColor(colors.HexColor('#666666'))
    for i in range(1,21):
        if i%5==0 or i in (1,20):
            c.drawCentredString(ox+(i-0.5)*CELL_MM*s, oy-2.2*mm, str(i))
            c.drawCentredString(ox-2.2*mm, oy+(i-0.5)*CELL_MM*s, str(i))
    # Placa base trasera 120x100 (centrada en estación)
    bcx, bcy = ox+STATION_X*s, oy+STATION_Y*s  # centro del eje
    bx1, bx2 = bcx-60*s, bcx+60*s
    by1, by2 = bcy-50*s, bcy+50*s
    for x1,y1,x2,y2 in [(bx1,by1,bx2,by1),(bx1,by1,bx1,by2),(bx2,by1,bx2,by2),(bx1,by2,bx2,by2)]:
        line(c,x1,y1,x2,y2,0.9, colors.black)
    # Patitas/corner holes visual: agujeros esquina
    for (hx,hy) in [(bx1+5*s,by1+5*s),(bx2-5*s,by1+5*s),(bx1+5*s,by2-5*s),(bx2-5*s,by2-5*s)]:
        c.circle(hx,hy,1.6*s,stroke=1,fill=0)
    dim_text(c, (bx1+bx2)/2, by1-3.5*mm, 'PLACA BASE TRASERA — 120 × 100 mm', 6)
    # Estación
    c.setFillColor(colors.HexColor('#FF6B6B')); c.circle(bcx,bcy,11*mm,stroke=1,fill=1)
    c.setFillColor(colors.black); dim_text(c, bcx, bcy, 'PAN', 6)
    c.setFillColor(colors.HexColor('#E53935'))
    c.circle(bcx,bcy,3.5*mm,stroke=0,fill=1)
    dim_text(c, bcx, bcy+16*mm, 'Eje Pan (X=100, Y=-65)', 6)
    # Cotas tablero
    arrow_dim_h(c, ox, ox+200*s, oy+215*s, '200 mm', 7)
    arrow_dim_v(c, oy, oy+200*s, ox-12*mm, '200 mm', 7)
    # Espesor típico
    dim_text(c, ox+100*s, oy+225*s, 'Tablero activo 20×20 = 200×200 mm  (celdas 10×10 mm)  •  400 casillas', 7)
    # Corte A-A marcador
    c.setStrokeColor(colors.HexColor('#1976D2')); c.setLineWidth(0.6); c.setDash(4,3)
    line(c, bcx, oy-8*mm, bcx, oy+230*mm, 0.6, colors.HexColor('#1976D2'))
    c.setDash()
    c.setFillColor(colors.HexColor('#1976D2')); c.setFont('Helvetica-Bold',7)
    c.drawString(bcx+2*mm, oy+232*mm, 'A')
    c.drawString(bcx+2*mm, oy-10*mm, 'A')
    # Cotas estación respecto a tablero
    line(c, bx1, bcy, bx2, bcy, 0.35, colors.HexColor('#666666'))
    arrow_dim_h(c, bcx-60*s, bcx+60*s, bcy-58*mm, '120 mm', 6)
    arrow_dim_v(c, by1, by2, bx1-8*mm, '100 mm', 6)
    # Leyenda
    lx, ly = 320*mm, 210*mm
    c.setFont('Helvetica-Bold', 7); c.drawString(lx, ly, 'Leyenda planta')
    c.setFont('Helvetica', 6.5)
    c.drawString(lx, ly-5*mm, '• Tablero: 200×200, rejilla 10 mm, 400 celdas')
    c.drawString(lx, ly-10*mm, '• Placa trasera: 120×100, espesor 4–5 mm (MDF/contrachapado)')
    c.drawString(lx, ly-15*mm, '• Estación eje Pan en (100, -65) Y=-65 → 65 mm por detrás del borde')
    c.drawString(lx, ly-20*mm, '• Agujeros base Ø3.2 mm (M3) en esquinas a 5 mm del borde')
    c.drawString(lx, ly-25*mm, '• Corte A-A = elevación frontal (ver pág. 2)')
    # Seguridad rayo
    c.setFont('Helvetica-Bold', 6.5); c.drawString(lx, ly-35*mm, 'Seguridad del rayo:')
    c.setFont('Helvetica', 6)
    c.drawString(lx, ly-40*mm, '• Pan ±57°, Tilt 30–72° → el cono queda dentro del tablero.')
    c.drawString(lx, ly-45*mm, '  Ver TEORIA_CINEMATICA.md y PLAN_ELECTRONICO.md')
    c.showPage()

    # =============== PAGINA 2: Corte A-A elevación ===============
    header_footer(c, 2, pages, W, H, 'Corte A-A — Elevación Frontal (corte por el eje de la torreta)')
    # Eje de corte es vertical en X=100. Vista de perfil: DISTANCIA (Y,Z)
    # Tablero: Y 0..200, Z 0 (espesor)
    s=1.0*mm
    ox, oy = 70*mm, 70*mm  # origen Y=0,Z=0
    # Suelo
    line(c, ox-30*mm, oy, ox+260*mm, oy, 0.9)
    # Tablero perfil
    line(c, ox, oy, ox+200*s, oy, 0.9); line(c, ox, oy+4*mm, ox+200*s, oy+4*mm, 0.4)
    line(c, ox, oy, ox, oy+4*mm, 0.9); line(c, ox+200*s, oy, ox+200*s, oy+4*mm, 0.9)
    # Placa base
    line(c, ox-90*mm, oy, ox+50*mm, oy, 0.9)
    line(c, ox-90*mm, oy+5*mm, ox+50*mm, oy+5*mm, 0.4)
    # Torreta: bloque base + estructura tilt H=180
    # Base 60x60
    b1x, b1y = ox-35*mm, oy+5*mm
    line(c, b1x, b1y, b1x+70*mm, b1y, 0.9); line(c, b1x, b1y, b1x, b1y+40*mm, 0.9); line(c, b1x+70*mm, b1y, b1x+70*mm, b1y+40*mm, 0.9)
    line(c, b1x, b1y+40*mm, b1x+70*mm, b1y+40*mm, 0.9)
    # Eje tilt a H=180
    tilt_y = oy+180*mm
    c.setFillColor(colors.HexColor('#4CAF50')); c.circle(b1x+35*mm, tilt_y, 9*mm, stroke=1, fill=1)
    c.setFillColor(colors.black); dim_text(c, b1x+35*mm, tilt_y, 'TILT', 6)
    # Eje pan vs tilt
    c.setFillColor(colors.HexColor('#FF6B6B')); c.circle(b1x+35*mm, oy+25*mm, 10*mm, stroke=1, fill=1)
    c.setFillColor(colors.black); dim_text(c, b1x+35*mm, oy+25*mm, 'PAN', 5)
    # Soporte lateral (U)
    line(c, b1x, tilt_y, b1x+10*mm, tilt_y, 0.9); line(c, b1x+60*mm, tilt_y, b1x+70*mm, tilt_y, 0.9)
    # Láser
    c.setStrokeColor(colors.red); c.setLineWidth(0.9)
    laser_x = b1x+35*mm; laser_y = tilt_y
    line(c, laser_x, laser_y, laser_x+260*mm, laser_y-100*mm, 0.9, colors.red)
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.red); c.circle(laser_x, laser_y, 2.2*mm, stroke=1, fill=1)
    dim_text(c, laser_x+18*mm, laser_y+6*mm, 'Láser KY-008', 6)
    # Ángulo tilt
    line(c, laser_x, laser_y, laser_x+80*mm, laser_y, 0.35, colors.black)
    # arco
    c.setStrokeColor(colors.HexColor('#1976D2'))
    # aproximación de arco con puntos
    import math as _m
    for d in range(30,73,2):
        ang=_m.radians(d)
        # puntos sobre arco radio 60mm según tilt
        # línea de referencia horizontal: x+60cos, y-60sin (abajo)
        pass
    c.setStrokeColor(colors.black)
    # Cotas altura
    arrow_dim_v(c, oy, tilt_y, ox-45*mm, '180 mm (TILT_H)', 7)
    dim_text(c, b1x+35*mm, oy-8*mm, 'Base 70×40', 6)
    dim_text(c, ox+100*mm, oy+12*mm, 'Tablero espesor 4–5 mm', 6)
    # Piezas
    lx, ly = 330*mm, 200*mm
    c.setFont('Helvetica-Bold', 7); c.drawString(lx, ly, 'Piezas del corte A-A')
    c.setFont('Helvetica', 6.5)
    items=[
        'P1 Placa base 120×100×5',
        'P2 Columna base torreta 70×40×5',
        'P3 Soporte U lateral (2×) para eje tilt',
        'P4 Torreta Pan: disco Ø40 + escuadra',
        'Tablero 200×200×5 (encajado en marco pág.3)',
    ]
    for i,t in enumerate(items): c.drawString(lx, ly-(i+1)*5*mm, '• '+t)
    c.setFont('Helvetica', 6)
    c.drawString(lx, ly-35*mm, '• Altura eje tilt: 180 mm sobre plano del tablero.')
    c.drawString(lx, ly-40*mm, '• Verágenes: pan 90°=frente, tilt 90°=horizontal (servo).')
    c.showPage()

    # =============== PAGINA 3: Despiece marco y tablero ===============
    header_footer(c, 3, pages, W, H, 'Despiece — Marco del Tablero y Placa Trasera (Escala 1:1)')
    # Marco: tablero 200x200 + margen 10mm por lado => 220x220 externo
    ox, oy = 60*mm, 50*mm
    s=1.0*mm
    # Marco externo
    line(c, ox, oy, ox+220*s, oy, 0.9); line(c, ox, oy, ox, oy+220*s, 0.9); line(c, ox+220*s, oy, ox+220*s, oy+220*s, 0.9); line(c, ox, oy+220*s, ox+220*s, oy+220*s, 0.9)
    # Hueco interno
    c.setStrokeColor(colors.HexColor('#E65100')); c.setLineWidth(0.9)
    line(c, ox+10*s, oy+10*s, ox+210*s, oy+10*s, 0.9, colors.HexColor('#E65100'))
    line(c, ox+10*s, oy+10*s, ox+10*s, oy+210*s, 0.9, colors.HexColor('#E65100'))
    line(c, ox+210*s, oy+10*s, ox+210*s, oy+210*s, 0.9, colors.HexColor('#E65100'))
    line(c, ox+10*s, oy+210*s, ox+210*s, oy+210*s, 0.9, colors.HexColor('#E65100'))
    c.setStrokeColor(colors.black)
    dim_text(c, ox+110*s, oy+235*s, 'MARCO EXTERNO 220 × 220 mm', 7)
    dim_text(c, ox+110*s, oy+100*s, 'Hueco 200 × 200 mm (tablero)', 6)
    # Listones: 4 de 220x10 + 2 de 200x10
    dim_text(c, ox+110*s, oy+233*s, 'Listón sup. 220×10', 5)
    dim_text(c, ox+110*s, oy-8*mm, 'Listón inf. 220×10', 5)
    dim_text(c, ox-10*mm, oy+110*s, 'Lateral 200×10', 5, 90)
    dim_text(c, ox+230*s, oy+110*s, 'Lateral 200×10', 5, 90)
    # Agujeros marco para tornillos M3
    for (hx,hy) in [(ox+5*s,oy+5*s),(ox+215*s,oy+5*s),(ox+5*s,oy+215*s),(ox+215*s,oy+215*s)]:
        c.circle(hx,hy,1.6*s,stroke=1,fill=0)
    # Placa trasera a la derecha
    px, py = 320*mm, 50*mm
    line(c, px, py, px+120*s, py, 0.9); line(c, px, py, px, py+100*s, 0.9); line(c, px+120*s, py, px+120*s, py+100*s, 0.9); line(c, px, py+100*s, px+120*s, py+100*s, 0.9)
    dim_text(c, px+60*s, py+115*s, 'PLACA TRASERA 120 × 100', 7)
    for (hx,hy) in [(px+8*s,py+8*s),(px+112*s,py+8*s),(px+8*s,py+92*s),(px+112*s,py+92*s)]:
        c.circle(hx,hy,1.6*s,stroke=1,fill=0)
    # Señal de centro
    c.setStrokeColor(colors.red)
    line(c, px+60*s, py+95*s, px+60*s, py+105*s,0.4, colors.red); line(c, px+55*s, py+100*s, px+65*s, py+100*s,0.4, colors.red)
    c.setStrokeColor(colors.black)
    dim_text(c, px+60*s, py+105*s, 'Centro (X=100)', 5)
    c.showPage()

    # =============== PAGINA 4: Torreta despiece y cotas ===============
    header_footer(c, 4, pages, W, H, 'Despiece — Torreta Pan-Tilt y Soporte del Láser (Escala 1:1)')
    # Disco pan
    ox, oy = 80*mm, 100*mm
    c.setFillColor(colors.HexColor('#FFE082')); c.circle(ox,oy,40*mm,stroke=1,fill=1)
    c.setFillColor(colors.black); dim_text(c, ox, oy, 'DISCO PAN Ø80', 7)
    for a in [0,90,180,270]:
        x=ox+30*mm*math.cos(math.radians(a)); y=oy+30*mm*math.sin(math.radians(a))
        c.circle(x,y,1.8*mm,stroke=1,fill=0)
    dim_text(c, ox, oy+50*mm, 'Disco Ø80 × 5 mm — 4× M3 a 30 mm radio',6)
    # Eje servo
    c.setFillColor(colors.HexColor('#FF6B6B')); c.circle(ox,oy,12*mm,stroke=1,fill=1)
    c.setFillColor(colors.black); dim_text(c, ox, oy, 'PAN',6)
    # Soporte U tilt a la derecha
    ux, uy = 260*mm, 90*mm
    line(c, ux, uy, ux+90*mm, uy, 0.9); line(c, ux, uy, ux, uy+70*mm, 0.9); line(c, ux+90*mm, uy, ux+90*mm, uy+70*mm, 0.9)
    line(c, ux, uy+70*mm, ux+90*mm, uy+70*mm, 0.9)
    dim_text(c, ux+45*mm, uy+82*mm, 'SOPORTE U TILT 90 × 70 (2×)',7)
    c.setFillColor(colors.HexColor('#81C784')); c.circle(ux+45*mm, uy+35*mm, 9*mm, stroke=1, fill=1)
    c.setFillColor(colors.black); dim_text(c, ux+45*mm, uy+35*mm, 'TILT',6)
    # Láser bracket
    c.setStrokeColor(colors.red); c.setLineWidth(0.9)
    c.circle(ux+45*mm, uy+35*mm+18*mm, 5*mm, stroke=1, fill=0)
    c.setStrokeColor(colors.black)
    dim_text(c, ux+45*mm, uy+35*mm+28*mm, 'Soporte láser Ø12, H 18',6)
    # Lista corte
    lx, ly = 380*mm, 200*mm
    c.setFont('Helvetica-Bold',7); c.drawString(lx, ly, 'Piezas')
    c.setFont('Helvetica',6.5)
    for i,t in enumerate(['P4 Disco pan Ø80','P5 U tilt 90×70 (2)','P6 Escuadra láser','P7 Base servo (60×40)','Tornillería M3/M2.6']):
        c.drawString(lx, ly-(i+1)*5*mm, '• '+t)
    c.showPage()

    # =============== PAGINA 5: Diagrama electrónico (ESQUEMA, NO 1:1) ===============
    header_footer(c, 5, pages, W, H, 'Esquema Electrónico y Mapa de Pines (NO a escala — referencia)')
    # Bloques ESP32
    bx, by = 60*mm, 70*mm
    # ESP32
    line(c, bx, by, bx+70*mm, by, 0.9); line(c, bx, by, bx, by+90*mm, 0.9); line(c, bx+70*mm, by, bx+70*mm, by+90*mm, 0.9); line(c, bx, by+90*mm, bx+70*mm, by+90*mm, 0.9)
    dim_text(c, bx+35*mm, by+100*mm, 'ESP32 WROOM-32',7)
    pins=[
        ('GPIO18', by+75*mm, '→ PAN servo'),
        ('GPIO19', by+68*mm, '→ TILT servo'),
        ('GPIO23', by+61*mm, '→ LÁSER (2N2222A)'),
        ('GPIO21', by+54*mm, '→ Buzzer'),
        ('GPIO22', by+47*mm, '→ LED acierto'),
        ('GPIO25', by+40*mm, 'BT TEST'),
        ('GPIO26', by+33*mm, 'MAINT/GND'),
        ('GPIO34', by+26*mm, 'ADC LDR / VSENSE'),
    ]
    c.setFont('Helvetica',6)
    for name,y,desc in pins:
        c.drawString(bx+4*mm, y, name)
        dim_text(c, bx+58*mm, y, desc, 4.5)
    # Alimentación
    ax, ay= 200*mm, 120*mm
    line(c, ax, ay, ax+90*mm, ay, 0.8); line(c, ax, ay, ax, ay+60*mm, 0.8); line(c, ax+90*mm, ay, ax+90*mm, ay+60*mm, 0.8); line(c, ax, ay+60*mm, ax+90*mm, ay+60*mm, 0.8)
    dim_text(c, ax+45*mm, ay+70*mm, 'Fuente 6V/4A + Buck 5V',7)
    c.setFont('Helvetica',6)
    c.drawString(ax+5*mm, ay+45*mm, '• Riel 6V → servos (1000µF)')
    c.drawString(ax+5*mm, ay+38*mm, '• Riel 5V → ESP32/láser/buzzer (470µF)')
    c.drawString(ax+5*mm, ay+31*mm, '• GND COMÚN (estrella)')
    c.drawString(ax+5*mm, ay+24*mm, '• NO alimentar servos desde ESP32')
    # Sensado LDR hint
    mx, my= 330*mm, 120*mm
    line(c, mx, my, mx+70*mm, my, 0.8); line(c, mx, my, mx, my+60*mm, 0.8); line(c, mx+70*mm, my, mx+70*mm, my+60*mm, 0.8); line(c, mx, my+60*mm, mx+70*mm, my+60*mm, 0.8)
    dim_text(c, mx+35*mm, my+70*mm, 'Matriz LDR 20×20',7)
    c.setFont('Helvetica',6)
    c.drawString(mx+5*mm, my+48*mm, '• 25× CD74HC4067 (16ch)')
    c.drawString(mx+5*mm, my+41*mm, '• 4 líneas S0–S3 compartidas')
    c.drawString(mx+5*mm, my+34*mm, '• SIG → GPIO34 (ADC1)')
    c.drawString(mx+5*mm, my+27*mm, '• LDR+10kΩ divisor 3.3V')
    c.drawString(mx+5*mm, my+20*mm, '• ΔV láser>threshold')
    c.showPage()

    # =============== PAGINA 6: Lista de materiales y notas ===============
    header_footer(c, 6, pages, W, H, 'Lista de Materiales, Tolerancias y Notas de Fabricación')
    # Tabla BOM
    x0,y0=20*mm, 200*mm; cw=[12*mm,78*mm,18*mm,28*mm,52*mm]; rh=7*mm
    headers=['Ref','Pieza / Componente','Cant.','Dimensión','Notas / Tolerancia']
    # header bg
    c.setFillColor(colors.HexColor('#EEEEEE')); c.rect(x0,y0-5*mm,sum(cw),rh,stroke=1,fill=1)
    c.setFillColor(colors.black); c.setFont('Helvetica-Bold',6.5)
    xx=x0
    for i,h in enumerate(headers):
        c.drawString(xx+1*mm, y0, h); xx+=cw[i]
    rows=[
        ['P1','Placa base trasera MDF/contrachapado','1','120×100×5','Taladros Ø3.2 (M3) c/esquinas'],
        ['P2','Columna base torreta','1','70×40×5','Atornillada a P1'],
        ['P3','Soporte U lateral tilt','2','90×70×4','Eje tilt a 180 mm s/plano'],
        ['P4','Disco pan','1','Ø80×5','4×Ø3.2 a r=30 mm'],
        ['P5','Escuadra soporte láser','1','L 40×25×3','Ajuste fino Y'],
        ['P6','Marco tablero (listones)','4+2','220×10 / 200×10','Hueco 200×200 exacto'],
        ['P7','Tablero activo','1','200×200×5','Rejilla 10 mm; LDR por celda'],
        ['E1','ESP32 WROOM-32','2 (A/B)','DevKit','GPIO 18,19,23,21,22,25,26,34'],
        ['E2','Servo MG996R pan / MG90S tilt','1+1','6 V','PWM 500–2500 µs, 50 Hz'],
        ['E3','Láser KY-008 650nm 5mW','1','5 V','2N2222A +1kΩ +10kΩ pull-down'],
        ['E4','Zumbador activo + LED','1+1','5 V','LED 330Ω a GPIO22'],
        ['E5','Fuente 6V/4A + Buck 5V/3A','1','—','1000µF servos, 470µF ESP32'],
        ['E6','CD74HC4067 MUX 16ch','25','DIP-24','Para 400 LDR (400/16)'],
        ['E7','LDR 5 mm + R 10 kΩ','400','—','Divisor 3.3V por celda'],
    ]
    y=y0-rh
    c.setFont('Helvetica',6)
    for r in rows:
        if y<25*mm: break
        # zebra
        # if row index even fill light
        xx=x0
        for i,cell in enumerate(r):
            c.drawString(xx+1*mm, y, str(cell)); xx+=cw[i]
        y-=rh
    # Tolerancias texto
    y=max(y-6*mm, 90*mm)
    c.setFont('Helvetica-Bold',8); c.drawString(20*mm,y,'Tolerancias y notas'); y-=5*mm
    c.setFont('Helvetica',6.5)
    notes=[
        '• Tolerancia general de corte: ±0.5 mm en tablero/marco; ±1.0 mm en placa base y soportes.',
        '• Taladros: Ø3.2 mm para M3, Ø2.6 mm para M2.6 en servo. Avellanado visual.',
        '• Altura eje tilt: 180 mm sobre el plano del tablero (TILT_H_MM). Verificar con calibre.',
        '• Evitar strapping (0,2,12,15), flash (6–11) y usar solo ADC1 para entradas analógicas.',
        '• GND común en estrella; cables de servo ≤30 cm; condensadores junto a servos y ESP32.',
        '• Láser: seguridad 5 mW — no mirar directamente; montaje con brida y tapa anti-reflejo.',
        '• Si se cambia estación (X,Y,H), actualizar CAL SET (trims ±10°) y regenerar plano.',
    ]
    for n in notes:
        c.drawString(20*mm, y, n); y-=4.5*mm
    c.showPage()
    c.save()
    print('Generated:', OUT, os.path.getsize(OUT), 'bytes')

if __name__=='__main__':
    build()
