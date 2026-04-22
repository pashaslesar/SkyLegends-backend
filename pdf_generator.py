from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
import io
from datetime import datetime, timedelta

# ─── Colors ───────────────────────────────────────────────────────────────────
C_DARK    = colors.HexColor("#0f172a")
C_BLUE    = colors.HexColor("#0ea5e9")
C_BLUE_LT = colors.HexColor("#e0f2fe")
C_GREY    = colors.HexColor("#64748b")
C_LGREY   = colors.HexColor("#f1f5f9")
C_WHITE   = colors.white
C_GREEN   = colors.HexColor("#10b981")

PRICE_PER_M2 = 39

def generate_invoice_pdf(order: dict, client: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=22*mm, rightMargin=22*mm,
        topMargin=18*mm, bottomMargin=18*mm
    )

    W = A4[0] - 44*mm  # usable width

    # ─── Styles ───────────────────────────────────────────────────────────────
    def st(name, **kw):
        return ParagraphStyle(name, **kw)

    S_logo   = st("logo",  fontName="Helvetica-Bold", fontSize=22, textColor=C_BLUE)
    S_tag    = st("tag",   fontName="Helvetica",      fontSize=8,  textColor=C_GREY,  spaceAfter=0)
    S_h1     = st("h1",   fontName="Helvetica-Bold", fontSize=13, textColor=C_DARK, spaceBefore=6)
    S_label  = st("lbl",  fontName="Helvetica-Bold", fontSize=7,  textColor=C_GREY,  spaceAfter=1,
                  wordWrap="LTR", leading=10)
    S_val    = st("val",  fontName="Helvetica",      fontSize=9,  textColor=C_DARK,  leading=13)
    S_small  = st("sm",   fontName="Helvetica",      fontSize=7,  textColor=C_GREY,  leading=10)
    S_note   = st("note", fontName="Helvetica",      fontSize=8,  textColor=C_GREY,  leading=12)

    story = []

    # ─── HEADER ───────────────────────────────────────────────────────────────
    now = datetime.now()
    due = now + timedelta(days=14)
    order_num = order.get("order_num", "AW-000001")
    vs = order_num.replace("AW-", "")

    header_data = [
        [
            Paragraph("AEROWASH", S_logo),
            "",
            Table([
                [Paragraph("FAKTURA", st("fi", fontName="Helvetica-Bold", fontSize=8, textColor=C_GREY)),
                 Paragraph(order_num, st("fn", fontName="Helvetica-Bold", fontSize=16, textColor=C_BLUE))],
                [Paragraph("Datum vystavení", S_label),
                 Paragraph(now.strftime("%d.%m.%Y"), S_val)],
                [Paragraph("Datum splatnosti", S_label),
                 Paragraph(due.strftime("%d.%m.%Y"), S_val)],
                [Paragraph("Variabilní symbol", S_label),
                 Paragraph(vs, S_val)],
            ], colWidths=[32*mm, 38*mm], style=TableStyle([
                ("ALIGN", (1,0), (1,-1), "RIGHT"),
                ("TOPPADDING", (0,0), (-1,-1), 2),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ]))
        ]
    ]
    ht = Table(header_data, colWidths=[55*mm, None, 72*mm])
    ht.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(ht)
    story.append(Paragraph("Profesionální mytí fasád a oken drony", S_tag))
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_BLUE, spaceAfter=6*mm))

    # ─── PARTIES ──────────────────────────────────────────────────────────────
    def info_block(title, lines):
        rows = [[Paragraph(title, st("pt", fontName="Helvetica-Bold", fontSize=7,
                                     textColor=C_BLUE, spaceAfter=3))]]
        for label, val in lines:
            if val:
                rows.append([Paragraph(f"<b>{label}</b>  {val}", S_note)])
        return Table(rows, colWidths=[(W/2)-5*mm], style=TableStyle([
            ("TOPPADDING", (0,0), (-1,-1), 1),
            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
            ("BACKGROUND", (0,0), (0,0), C_LGREY),
            ("LEFTPADDING", (0,0), (-1,-1), 4),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ]))

    supplier = info_block("DODAVATEL", [
        ("Firma:", "AeroWash s.r.o."),
        ("Adresa:", "Na Příkopě 15, 110 00 Praha 1"),
        ("IČO:", "08765432"),
        ("DIČ:", "CZ08765432"),
        ("E-mail:", "info@aerowash.cz"),
        ("Tel:", "+420 800 123 456"),
    ])

    client_lines = [
        ("Jméno:", client.get("name", "")),
        ("Firma:", client.get("company", "")),
        ("Adresa:", client.get("billing_address", "")),
        ("IČO:", client.get("ico", "")),
        ("E-mail:", client.get("email", "")),
        ("Tel:", client.get("phone", "")),
    ]
    buyer = info_block("ODBĚRATEL", client_lines)

    parties = Table([[supplier, "", buyer]], colWidths=[(W/2)-3*mm, 6*mm, (W/2)-3*mm])
    parties.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(parties)
    story.append(Spacer(1, 7*mm))

    # ─── SERVICE LOCATION ─────────────────────────────────────────────────────
    location = order.get("location", "")
    if location:
        loc_t = Table([[
            Paragraph("📍  Místo provedení služby:", st("lh", fontName="Helvetica-Bold",
                      fontSize=8, textColor=C_GREY)),
            Paragraph(location, S_val),
        ]], colWidths=[52*mm, W-52*mm])
        loc_t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), C_LGREY),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ROUNDEDCORNERS", [3], ),
        ]))
        story.append(loc_t)
        story.append(Spacer(1, 6*mm))

    # ─── ITEMS TABLE ──────────────────────────────────────────────────────────
    facade  = float(order.get("facade_area", 0))
    windows = float(order.get("window_area", 0))
    total   = (facade + windows) * PRICE_PER_M2

    col_w = [W - 85*mm, 28*mm, 25*mm, 30*mm]
    items_header = ["Popis služby", "Plocha (m²)", "Cena / m²", "Celkem"]
    rows = [items_header]

    if facade > 0:
        rows.append(["Mytí fasády dronem", f"{facade:,.1f}", f"{PRICE_PER_M2} Kč",
                      f"{facade*PRICE_PER_M2:,.0f} Kč"])
    if windows > 0:
        rows.append(["Mytí oken dronem", f"{windows:,.1f}", f"{PRICE_PER_M2} Kč",
                      f"{windows*PRICE_PER_M2:,.0f} Kč"])
    # subtotal row
    rows.append(["", f"{facade+windows:,.1f} m²", "", f"{total:,.0f} Kč"])

    items_t = Table(rows, colWidths=col_w, repeatRows=1)
    n = len(rows)
    items_t.setStyle(TableStyle([
        # header
        ("BACKGROUND",    (0,0), (-1,0),   C_DARK),
        ("TEXTCOLOR",     (0,0), (-1,0),   C_WHITE),
        ("FONTNAME",      (0,0), (-1,0),   "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),   8),
        ("TOPPADDING",    (0,0), (-1,0),   8),
        ("BOTTOMPADDING", (0,0), (-1,0),   8),
        # data rows
        ("FONTNAME",      (0,1), (-1,-2),  "Helvetica"),
        ("FONTSIZE",      (0,1), (-1,-2),  9),
        ("TOPPADDING",    (0,1), (-1,-2),  7),
        ("BOTTOMPADDING", (0,1), (-1,-2),  7),
        ("ROWBACKGROUNDS",(0,1), (-1,-2),  [C_WHITE, C_LGREY]),
        # subtotal row
        ("BACKGROUND",    (0,-1), (-1,-1), C_BLUE_LT),
        ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,-1), (-1,-1), 10),
        ("TOPPADDING",    (0,-1), (-1,-1), 8),
        ("BOTTOMPADDING", (0,-1), (-1,-1), 8),
        ("TEXTCOLOR",     (3,-1), (3,-1),  C_BLUE),
        # alignment
        ("ALIGN",         (1,0), (-1,-1),  "CENTER"),
        ("ALIGN",         (3,0), (3,-1),   "RIGHT"),
        ("VALIGN",        (0,0), (-1,-1),  "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1),  8),
        ("RIGHTPADDING",  (0,0), (-1,-1),  8),
        # border
        ("LINEBELOW",     (0,-1), (-1,-1), 0, C_WHITE),
        ("BOX",           (0,0), (-1,-1),  0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(items_t)
    story.append(Spacer(1, 8*mm))

    # ─── TOTAL BOX ────────────────────────────────────────────────────────────
    total_t = Table([
        ["", "CELKOVÁ ČÁSTKA K ÚHRADĚ:", f"{total:,.0f} Kč"]
    ], colWidths=[W-85*mm, 55*mm, 30*mm])
    total_t.setStyle(TableStyle([
        ("BACKGROUND",    (1,0), (-1,0), C_BLUE),
        ("TEXTCOLOR",     (1,0), (-1,0), C_WHITE),
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (1,0), (1,0),  9),
        ("FONTSIZE",      (2,0), (2,0),  14),
        ("ALIGN",         (1,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (1,0), (-1,-1), 8),
        ("RIGHTPADDING",  (1,0), (-1,-1), 8),
    ]))
    story.append(total_t)
    story.append(Spacer(1, 8*mm))

    # ─── PAYMENT INFO ─────────────────────────────────────────────────────────
    pay_data = [
        [
            Paragraph("PLATEBNÍ ÚDAJE", st("ph", fontName="Helvetica-Bold", fontSize=7, textColor=C_GREY)),
            Paragraph("TERMÍN PROVEDENÍ", st("ph2", fontName="Helvetica-Bold", fontSize=7, textColor=C_GREY)),
        ],
        [
            Paragraph(
                "Číslo účtu: <b>123-4567890/0800</b><br/>"
                "IBAN: <b>CZ65 0800 0000 1234 5678 90</b><br/>"
                f"Variabilní symbol: <b>{vs}</b>",
                S_note
            ),
            Paragraph(
                (f"Požadovaný termín: <b>{order.get('service_date','—')}</b><br/>" if order.get("service_date") else "Termín: <b>Dle dohody</b><br/>") +
                "Typ objektu: <b>" + (order.get("building_type","—")) + "</b><br/>" +
                (f"Počet podlaží: <b>{order.get('floors','—')}</b>" if order.get("floors") else ""),
                S_note
            ),
        ],
    ]
    pay_t = Table(pay_data, colWidths=[(W/2)-3*mm, (W/2)-3*mm],
                  style=TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  C_LGREY),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("BOX",           (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("LINEBETWEEN",   (0,0), (1,-1),  0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    story.append(pay_t)

    # ─── NOTES ────────────────────────────────────────────────────────────────
    if order.get("notes"):
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph(f"<b>Poznámky:</b> {order['notes']}", S_note))

    # ─── FOOTER ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=3*mm))
    story.append(Paragraph(
        "AeroWash s.r.o.  ·  Na Příkopě 15, 110 00 Praha 1  ·  IČO: 08765432  ·  "
        "info@aerowash.cz  ·  +420 800 123 456  ·  www.aerowash.cz",
        st("ft", fontName="Helvetica", fontSize=7, textColor=C_GREY,
           alignment=1)  # centered
    ))
    story.append(Paragraph(
        f"Dokument vygenerován automaticky dne {now.strftime('%d.%m.%Y %H:%M')}",
        st("ft2", fontName="Helvetica", fontSize=6, textColor=colors.HexColor("#94a3b8"),
           alignment=1, spaceBefore=2)
    ))

    doc.build(story)
    return buf.getvalue()
