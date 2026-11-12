"""Genera PDFs reproducibles a partir de materiales originales del proyecto."""

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]


def footer(canvas, document):
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#65736a"))
    canvas.drawString(48, 32, "Cuaderno | Material original de demostración | CC BY 4.0")
    canvas.drawRightString(A4[0] - 48, 32, str(document.page))


def generate():
    sources = json.loads((ROOT / "demo/source.json").read_text(encoding="utf-8"))
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "BodyDemo",
            fontName="Helvetica",
            fontSize=11,
            leading=17,
            textColor=colors.HexColor("#193e37"),
            spaceAfter=14,
        )
    )
    for filename, source in sources.items():
        story = []
        for index, page in enumerate(source["pages"]):
            if index:
                story.append(PageBreak())
            story.append(Paragraph(source["title"], styles["Heading3"]))
            story.append(Paragraph(page["title"], styles["Title"]))
            story.append(Spacer(1, 18))
            story.extend(Paragraph(text, styles["BodyDemo"]) for text in page["paragraphs"])
        output = ROOT / "demo" / filename
        SimpleDocTemplate(
            str(output),
            pagesize=A4,
            rightMargin=48,
            leftMargin=48,
            topMargin=48,
            bottomMargin=55,
        ).build(
            story,
            onFirstPage=footer,
            onLaterPages=footer,
            canvasmaker=lambda *args, **kwargs: canvas.Canvas(*args, **{**kwargs, "invariant": 1}),
        )
        print(output)


if __name__ == "__main__":
    generate()
