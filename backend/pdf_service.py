from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm
import datetime
from io import BytesIO

def generar_certificado_pdf(postulacion_id: int, nombre_estudiante: str, convocatoria: str, universidad: str, pais: str) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4

    # Colores
    azul_oscuro = HexColor("#1A3A6B")
    azul_medio = HexColor("#2563EB")
    azul_claro = HexColor("#EFF6FF")
    amarillo = HexColor("#FFC107")
    verde = HexColor("#22C55E")
    gris_texto = HexColor("#64748B")
    gris_borde = HexColor("#DCDCDC")
    gris_fondo = HexColor("#F9FAFB")

    # --- Header ---
    c.setFillColor(azul_oscuro)
    c.rect(0, H - 22*mm, W, 22*mm, fill=1, stroke=0)

    # Logo texto
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(12*mm, H - 14*mm, "■  Intercambios UPC")

    # Badge "CERTIFICACIÓN OFICIAL"
    c.setFillColor(amarillo)
    badge_w, badge_h = 52*mm, 9*mm
    c.roundRect(W - badge_w - 13*mm, H - 7*mm - badge_h, badge_w, badge_h, 4*mm, fill=1, stroke=0)
    c.setFillColor(azul_oscuro)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(W - 13*mm - badge_w/2, H - 7*mm - badge_h/2 - 1.5*mm, "CERTIFICACIÓN OFICIAL")

    # Línea verde decorativa
    c.setFillColor(verde)
    c.rect(0, H - 24*mm, W, 2*mm, fill=1, stroke=0)

    # --- Cuerpo (Borde) ---
    c.setStrokeColor(gris_borde)
    c.setLineWidth(0.5)
    c.roundRect(15*mm, 15*mm, W - 30*mm, H - 65*mm, 4*mm, fill=0, stroke=1)

    # --- Contenido ---
    # Universidad
    c.setFillColor(gris_texto)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W/2, H - 48*mm, "UNIVERSIDAD PILOTO DE COLOMBIA")

    # Título
    c.setFillColor(azul_oscuro)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(W/2, H - 60*mm, "Certificado de Participación")
    c.drawCentredString(W/2, H - 70*mm, "en Intercambio Académico")

    # Estrella decorativa
    c.setFillColor(azul_oscuro)
    c.circle(W/2, H - 83*mm, 5*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W/2, H - 83*mm - 2*mm, "★")

    # Líneas decorativas
    c.setStrokeColor(HexColor("#C8C8C8"))
    c.setLineWidth(0.3)
    c.line(W/2 - 40*mm, H - 83*mm, W/2 - 12*mm, H - 83*mm)
    c.line(W/2 + 12*mm, H - 83*mm, W/2 + 40*mm, H - 83*mm)

    # "Se certifica que"
    c.setFillColor(gris_texto)
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, H - 97*mm, "Se certifica que el/la estudiante")

    # Nombre del estudiante
    c.setFillColor(azul_oscuro)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(W/2, H - 110*mm, nombre_estudiante)

    # Texto descripción
    c.setFillColor(HexColor("#505050"))
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, H - 122*mm, "completó satisfactoriamente su proceso de postulación y fue seleccionado/a")
    c.drawCentredString(W/2, H - 129*mm, "para participar en el siguiente programa de intercambio académico internacional.")

    # Caja programa
    c.setFillColor(azul_claro)
    c.setStrokeColor(HexColor("#93C5FD"))
    c.roundRect(25*mm, H - 137*mm - 32*mm, W - 50*mm, 32*mm, 3*mm, fill=1, stroke=1)
    
    c.setFillColor(azul_medio)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(W/2, H - 137*mm - 9*mm, "PROGRAMA DE INTERCAMBIO")
    
    c.setFillColor(azul_oscuro)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(W/2, H - 137*mm - 19*mm, convocatoria)
    
    c.setFillColor(azul_medio)
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, H - 137*mm - 27*mm, f"■ {universidad}  —  ■ {pais}")

    # Tres cajas: Período, Estado, Fecha
    ahora = datetime.datetime.now()
    mes_str = ahora.strftime("%b %Y").upper()
    semestre = "I" if ahora.month < 7 else "II"
    periodo = f"{ahora.year}-{semestre}"
    
    labels = ["PERÍODO", "ESTADO", "FECHA"]
    valores = [periodo, "APROBADO", mes_str]
    
    for i in range(3):
        x = 30*mm + i * 52*mm
        y = H - 177*mm - 22*mm
        c.setFillColor(gris_fondo)
        c.setStrokeColor(gris_borde)
        c.roundRect(x, y, 44*mm, 22*mm, 2*mm, fill=1, stroke=1)
        
        c.setFillColor(HexColor("#787878"))
        c.setFont("Helvetica", 7)
        c.drawCentredString(x + 22*mm, y + 15*mm, labels[i])
        
        if i == 1: # Estado verde
            c.setFillColor(HexColor("#16A34A"))
        else:
            c.setFillColor(azul_oscuro)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x + 22*mm, y + 6*mm, valores[i])

    # Sello circular
    c.setFillColor(azul_oscuro)
    c.circle(W/2, 60*mm, 12*mm, fill=1, stroke=0)
    c.setStrokeColor(amarillo)
    c.setLineWidth(1.5)
    c.circle(W/2, 60*mm, 12*mm, fill=0, stroke=1)
    
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W/2, 60*mm, "UPC")
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(W/2, 60*mm - 6*mm, "Sello Digital")

    # Firma
    c.setStrokeColor(HexColor("#B4B4B4"))
    c.setLineWidth(0.3)
    c.line(25*mm, 66*mm, 75*mm, 66*mm)
    c.setFillColor(azul_oscuro)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(25*mm, 60*mm, "Coordinador/a de Intercambios")
    c.setFillColor(HexColor("#646464"))
    c.setFont("Helvetica", 8)
    c.drawString(25*mm, 54*mm, "Dirección de Relaciones Internacionales")
    c.drawString(25*mm, 48*mm, "Universidad Piloto de Colombia")

    # Código de verificación
    codigo = f"UPC-INT-{ahora.year}-{str(postulacion_id).zfill(6)}"
    c.setFillColor(gris_fondo)
    c.setStrokeColor(HexColor("#C8C8C8"))
    c.roundRect(W - 93*mm, 57*mm, 68*mm, 14*mm, 2*mm, fill=1, stroke=1)
    c.setFillColor(HexColor("#787878"))
    c.setFont("Helvetica", 7)
    c.drawCentredString(W - 93*mm + 34*mm, 63*mm, "Código de verificación")
    c.setFillColor(azul_oscuro)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(W - 93*mm + 34*mm, 59*mm, codigo)

    # --- Footer ---
    c.setFillColor(azul_oscuro)
    c.rect(0, 0, W, 28*mm, fill=1, stroke=0)
    c.setFillColor(amarillo)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W/2, 11*mm, f"Universidad Piloto de Colombia  —  Programa de Desarrollo Web  —  {ahora.year}")
    c.setFillColor(HexColor("#C8DCFF"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(W/2, 4*mm, "Este certificado fue generado digitalmente y tiene validez oficial.")

    # Texto legal final
    c.setFillColor(HexColor("#969696"))
    c.setFont("Helvetica", 7)
    c.drawString(17*mm, 33*mm, "Generado automáticamente por Intercambios UPC · intercambiosupc.lat")
    c.drawRightString(W - 17*mm, 33*mm, ahora.strftime("%d/%m/%Y"))

    c.showPage()
    c.save()

    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content


def generar_ficha_estudiante_pdf(
    postulacion_id: int,
    nombre: str,
    email: str,
    cedula: str,
    celular: str,
    codigo: str,
    programa: str,
    semestre: int,
    convocatoria: str,
    universidad: str,
    pais: str,
    carta_intencion: str = None,
    documentos: list = None,
) -> bytes:
    """
    Genera un PDF con la ficha completa del estudiante para la universidad de destino.
    Incluye: datos personales, programa, semestre, carta de intención y lista de documentos.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4

    azul_oscuro = HexColor("#1A3A6B")
    azul_medio  = HexColor("#2563EB")
    azul_claro  = HexColor("#EFF6FF")
    amarillo    = HexColor("#FFC107")
    verde       = HexColor("#22C55E")
    gris_texto  = HexColor("#64748B")
    gris_borde  = HexColor("#DCDCDC")
    gris_fondo  = HexColor("#F9FAFB")

    # ── Header ──────────────────────────────────────────────────────────────
    c.setFillColor(azul_oscuro)
    c.rect(0, H - 22*mm, W, 22*mm, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(12*mm, H - 14*mm, "■  Intercambios UPC")

    c.setFillColor(amarillo)
    badge_w, badge_h = 62*mm, 9*mm
    c.roundRect(W - badge_w - 13*mm, H - 7*mm - badge_h, badge_w, badge_h, 4*mm, fill=1, stroke=0)
    c.setFillColor(azul_oscuro)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(W - 13*mm - badge_w/2, H - 7*mm - badge_h/2 - 1.5*mm, "FICHA DEL ESTUDIANTE")

    c.setFillColor(verde)
    c.rect(0, H - 24*mm, W, 2*mm, fill=1, stroke=0)

    # ── Título ──────────────────────────────────────────────────────────────
    y = H - 42*mm
    c.setFillColor(gris_texto)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W/2, y, "UNIVERSIDAD PILOTO DE COLOMBIA — OFICINA DE RELACIONES INTERNACIONALES")

    y -= 14*mm
    c.setFillColor(azul_oscuro)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(W/2, y, "Ficha de Estudiante Aprobado")

    y -= 10*mm
    c.setFont("Helvetica", 10)
    c.setFillColor(azul_medio)
    c.drawCentredString(W/2, y, f"Para: {universidad} — {pais}")

    # ── Datos personales ────────────────────────────────────────────────────
    y -= 18*mm
    c.setFillColor(azul_claro)
    c.setStrokeColor(HexColor("#93C5FD"))
    box_h = 62*mm
    c.roundRect(18*mm, y - box_h, W - 36*mm, box_h, 3*mm, fill=1, stroke=1)

    c.setFillColor(azul_medio)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(24*mm, y - 10*mm, "DATOS PERSONALES")

    c.setFont("Helvetica", 9.5)
    c.setFillColor(HexColor("#374151"))
    campos = [
        ("Nombre completo:", nombre),
        ("Correo electrónico:", email),
        ("Cédula / ID:", cedula),
        ("Teléfono:", celular),
        ("Código estudiantil:", codigo),
        ("Programa académico:", programa),
        ("Semestre cursando:", f"{semestre}°" if semestre else "—"),
    ]
    row_y = y - 22*mm
    col1_x = 26*mm
    col2_x = 72*mm
    for label, valor in campos:
        c.setFont("Helvetica", 8.5)
        c.setFillColor(gris_texto)
        c.drawString(col1_x, row_y, label)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(azul_oscuro)
        c.drawString(col2_x, row_y, str(valor))
        row_y -= 7*mm

    # ── Convocatoria ────────────────────────────────────────────────────────
    y = row_y - 6*mm
    c.setFillColor(gris_fondo)
    c.setStrokeColor(gris_borde)
    conv_h = 22*mm
    c.roundRect(18*mm, y - conv_h, W - 36*mm, conv_h, 3*mm, fill=1, stroke=1)

    c.setFillColor(azul_medio)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(24*mm, y - 8*mm, "CONVOCATORIA ASIGNADA")
    c.setFillColor(azul_oscuro)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(24*mm, y - 17*mm, convocatoria)

    # ── Documentos adjuntos ─────────────────────────────────────────────────
    y = y - conv_h - 10*mm
    c.setFillColor(azul_oscuro)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(18*mm, y, "Documentos Adjuntos")

    y -= 4*mm
    c.setStrokeColor(gris_borde)
    c.setLineWidth(0.5)
    c.line(18*mm, y, W - 18*mm, y)

    if documentos:
        for i, doc in enumerate(documentos):
            y -= 9*mm
            if y < 50*mm:
                c.showPage()
                y = H - 30*mm
            c.setFillColor(HexColor("#374151"))
            c.setFont("Helvetica", 9)
            c.drawString(22*mm, y, f"📄  {doc['tipo']}:")
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(azul_oscuro)
            c.drawString(75*mm, y, doc['nombre'])
    else:
        y -= 9*mm
        c.setFillColor(gris_texto)
        c.setFont("Helvetica", 9)
        c.drawString(22*mm, y, "No se adjuntaron documentos.")

    # ── Carta de intención (resumen) ────────────────────────────────────────
    if carta_intencion:
        y -= 16*mm
        c.setFillColor(azul_oscuro)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(18*mm, y, "Carta de Intención (extracto)")
        y -= 4*mm
        c.setStrokeColor(gris_borde)
        c.line(18*mm, y, W - 18*mm, y)
        y -= 6*mm

        c.setFillColor(HexColor("#374151"))
        c.setFont("Helvetica", 8.5)
        # Dividir en líneas de ~90 caracteres
        texto = carta_intencion[:600]
        if len(carta_intencion) > 600:
            texto += "..."
        palabras = texto.split()
        linea = ""
        for palabra in palabras:
            test = linea + " " + palabra if linea else palabra
            if c.stringWidth(test, "Helvetica", 8.5) < (W - 40*mm):
                linea = test
            else:
                c.drawString(22*mm, y, linea)
                y -= 5*mm
                linea = palabra
                if y < 45*mm:
                    break
        if linea:
            c.drawString(22*mm, y, linea)

    # ── Footer ──────────────────────────────────────────────────────────────
    ahora = datetime.datetime.now()
    c.setFillColor(azul_oscuro)
    c.rect(0, 0, W, 22*mm, fill=1, stroke=0)
    c.setFillColor(amarillo)
    c.setFont("Helvetica", 8)
    c.drawCentredString(W/2, 10*mm, f"Universidad Piloto de Colombia — Intercambios Académicos — {ahora.year}")
    c.setFillColor(HexColor("#C8DCFF"))
    c.setFont("Helvetica", 7)
    c.drawCentredString(W/2, 4*mm, "Documento generado automáticamente. Confidencial — solo para uso de la universidad de destino.")

    # Código de referencia
    ref = f"UPC-FICHA-{ahora.year}-{str(postulacion_id).zfill(6)}"
    c.setFillColor(HexColor("#969696"))
    c.setFont("Helvetica", 7)
    c.drawString(17*mm, 26*mm, f"Ref: {ref}")
    c.drawRightString(W - 17*mm, 26*mm, ahora.strftime("%d/%m/%Y %H:%M"))

    c.showPage()
    c.save()

    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content
