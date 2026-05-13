import io
import os
import PyPDF2
import requests
from io import BytesIO
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

logger = logging.getLogger(__name__)

try:
    from docx import Document
except ModuleNotFoundError:
    Document = None
    logger.error("Missing dependency: python-docx. Install with 'pip install python-docx'.")

class PDFService:
    def __init__(self):
        self.font_name = "Helvetica"
        self.rtl_font_name = "Helvetica"
        # Attempt to register fonts for PDF generation (optional but good for quality)
        self._init_fonts()

    def _init_fonts(self):
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont("DejaVuSans", path))
                    self.font_name = "DejaVuSans"
                    self.rtl_font_name = "DejaVuSans"
                    break
                except:
                    continue

    async def extract_text(self, file_path: str) -> dict:
        """
        Extract text from PDF or DOCX file.
        Supports local paths and URLs.
        """
        try:
            content = None
            if file_path.startswith(('http://', 'https://')):
                response = requests.get(file_path)
                response.raise_for_status()
                content = BytesIO(response.content)
                ext = file_path.split('.')[-1].lower()
            else:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
                with open(file_path, 'rb') as f:
                    content = BytesIO(f.read())
                ext = file_path.split('.')[-1].lower()

            if ext == 'pdf':
                return self._extract_from_pdf(content)
            elif ext in ['docx', 'doc']:
                return self._extract_from_docx(content)
            else:
                raise ValueError(f"Unsupported file extension: {ext}")

        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise Exception(f"Failed to extract text: {str(e)}")

    def _extract_from_pdf(self, content: BytesIO) -> dict:
        pdf_reader = PyPDF2.PdfReader(content)
        text = ""
        for page in pdf_reader.pages:
            text += (page.extract_text() or "") + "\n"
        
        return {
            "text": text.strip(),
            "page_count": len(pdf_reader.pages),
            "type": "pdf"
        }

    def _extract_from_docx(self, content: BytesIO) -> dict:
        if Document is None:
            raise ImportError("Missing python-docx dependency. Install it with: pip install python-docx")
        doc = Document(content)
        text = "\n".join([para.text for para in doc.paragraphs])
        return {
            "text": text.strip(),
            "page_count": 0, # Not applicable for docx in simple way
            "type": "docx"
        }

    def create_summary_pdf(self, title: str, summary: str, key_points: list, quizzes: list) -> bytes:
        """Generates a professional PDF report of the analysis"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin = 20 * mm
        y = height - margin
        
        # Title
        c.setFont(self.font_name, 16)
        c.drawString(margin, y, f"Report: {title}")
        y -= 15 * mm
        
        # Summary
        c.setFont(self.font_name, 12)
        c.drawString(margin, y, "Summary:")
        y -= 7 * mm
        y = self._draw_wrapped_text(c, summary, margin, y, width - 2*margin)
        y -= 10 * mm
        
        # Key Points
        if key_points:
            c.drawString(margin, y, "Key Points:")
            y -= 7 * mm
            for point in key_points:
                y = self._draw_wrapped_text(c, f"• {point}", margin + 5*mm, y, width - 2*margin - 5*mm)
                if y < margin: 
                    c.showPage()
                    y = height - margin
            y -= 10 * mm
            
        # Quizzes
        if quizzes:
            c.drawString(margin, y, "Quiz Questions:")
            y -= 7 * mm
            for i, q in enumerate(quizzes):
                question = f"{i+1}. {q.get('question')}"
                y = self._draw_wrapped_text(c, question, margin, y, width - 2*margin)
                for opt in q.get('options', []):
                    y = self._draw_wrapped_text(c, f"  - {opt}", margin + 5*mm, y, width - 2*margin - 5*mm)
                y -= 5 * mm
                if y < margin:
                    c.showPage()
                    y = height - margin

        c.save()
        buffer.seek(0)
        return buffer.read()

    def _draw_wrapped_text(self, c, text, x, y, max_width):
        lines = []
        words = str(text).split()
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            if pdfmetrics.stringWidth(test_line, self.font_name, 12) < max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        for line in lines:
            c.drawString(x, y, line)
            y -= 6 * mm
            if y < 20 * mm:
                c.showPage()
                y = A4[1] - 20 * mm
                c.setFont(self.font_name, 12)
        return y

pdf_service = PDFService()
