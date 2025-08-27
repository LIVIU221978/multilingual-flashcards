
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import mm
from io import BytesIO

def build_pdf_bytes(topic, language, cards):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h_style = styles["Heading2"]
    body = styles["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=9, leading=12)

    story = []
    story.append(Paragraph(f"Multilingual Flashcards — {language}", title_style))
    story.append(Paragraph(f"Topic: {topic}", h_style))
    story.append(Spacer(1, 6*mm))

    for idx, c in enumerate(cards, 1):
        term = c.get("term","(no term)")
        definition = c.get("definition","" )
        example = c.get("example","" )
        qa = c.get("qa", {}) if isinstance(c.get("qa", {}), dict) else {}
        question = qa.get("question","" )
        answer = qa.get("answer","" )

        story.append(Paragraph(f"{idx}. <b>{term}</b>", styles["Heading3"]))        
        data = [
            ["Definition", definition],
            ["Example", example],
            ["Q", question],
            ["A", answer]
        ]
        tbl = Table(data, colWidths=[28*mm, 150*mm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f0f4ff")),
            ("BOX", (0,0), (-1,-1), 0.6, colors.grey),
            ("INNERGRID", (0,0), (-1,-1), 0.3, colors.grey),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.Color(1,1,1)]),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 5*mm))

        if (idx % 6) == 0:
            story.append(PageBreak())

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf
