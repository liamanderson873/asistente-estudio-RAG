from io import BytesIO

import pytest
from reportlab.pdfgen.canvas import Canvas


@pytest.fixture
def pdf_bytes():
    def make(texts):
        buffer = BytesIO()
        canvas = Canvas(buffer)
        for text in texts:
            if text:
                canvas.drawString(50, 750, text)
            canvas.showPage()
        canvas.save()
        return buffer.getvalue()

    return make
