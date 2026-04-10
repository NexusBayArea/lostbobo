"""
PDF Service for SimHPC Platform

Generates professional PDF reports with Unicode support for engineering symbols.
Uses in-memory BytesIO buffer to avoid disk I/O in containerized environments.
"""

import io
import logging
from fpdf import FPDF
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_font_path(filename: str) -> Optional[Path]:
    """
    Resolve font path with multiple fallbacks.
    """
    local_path = Path(__file__).parent / "fonts" / filename
    if local_path.exists():
        return local_path

    logger.warning(f"Font {filename} not found. Falling back to system defaults.")
    return None


class SimHPCPDFReport(FPDF):
    """PDF report with Unicode support for engineering symbols."""

    def __init__(self):
        super().__init__()
        self.fonts_loaded = False

        # Add DejaVu Sans for Unicode support (Greek letters, etc.)
        try:
            # Try to load DejaVuSans.ttf
            font_path = get_font_path("DejaVuSans.ttf")
            if font_path:
                self.add_font("DejaVu", "", str(font_path), uni=True)

                # Try to load bold variant
                bold_path = get_font_path("DejaVuSans-Bold.ttf")
                if bold_path:
                    self.add_font("DejaVu", "B", str(bold_path), uni=True)

                # Try to load italic variant
                italic_path = get_font_path("DejaVuSans-Oblique.ttf")
                if italic_path:
                    self.add_font("DejaVu", "I", str(italic_path), uni=True)

                self.fonts_loaded = True
                logger.info("DejaVu fonts loaded successfully")
            else:
                logger.warning("Using built-in Helvetica – limited Unicode support")
        except Exception as e:
            logger.warning(
                f"Failed to load custom fonts, using built-in Helvetica fallback: {e}"
            )

    def safe_set_font(self, family: str, style: str = "", size: int = 12):
        """Sets font safely, falling back to Helvetica if custom font not loaded."""
        if self.fonts_loaded and family == "DejaVu":
            self.set_font("DejaVu", style, size)
        else:
            # Fallback to standard Helvetica
            fallback_style = style
            # FPDF uses 'B', 'I', 'U' or combinations.
            # Helvetica supports these standard styles.
            self.set_font("Helvetica", fallback_style, size)

    def header(self):
        self.safe_set_font("DejaVu", "B", 15)
        self.set_text_color(15, 23, 42)  # Dark Slate
        self.cell(0, 10, "SimHPC Platform - Engineering Analysis Report", 0, 1, "L")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.safe_set_font("DejaVu", "I", 8)
        self.set_text_color(100)
        self.cell(
            0,
            10,
            f"Page {self.page_no()} | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            0,
            0,
            "C",
        )


def generate_pdf_report(
    report_data: Dict[str, Any], output_path: Path = None, use_buffer: bool = True
) -> io.BytesIO | Path:
    """
    Generates a professional PDF report from simulation AI insights.

    Args:
        report_data: Dictionary containing report sections and metadata
        output_path: Optional path to save file (if use_buffer=False)
        use_buffer: If True, returns BytesIO buffer; if False, writes to output_path

    Returns:
        BytesIO buffer if use_buffer=True, otherwise Path to saved file
    """
    pdf = SimHPCPDFReport()
    pdf.add_page()

    # Metadata section
    pdf.safe_set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, f"Report ID: {report_data.get('report_id', 'N/A')}", 0, 1)

    pdf.safe_set_font("DejaVu", "", 10)
    pdf.cell(
        0, 10, f"Analysis Timestamp: {report_data.get('generated_at', 'N/A')}", 0, 1
    )

    # Add metadata flags if present
    metadata = report_data.get("metadata", {})
    if metadata.get("llm_generation_failed"):
        pdf.set_text_color(200, 50, 50)  # Red for warning
        pdf.cell(0, 10, "⚠ AI Generation Failed - Manual Interpretation Required", 0, 1)
        pdf.set_text_color(0, 0, 0)  # Reset

    if metadata.get("manual_review_required"):
        pdf.set_text_color(200, 100, 0)  # Orange for notice
        pdf.cell(0, 10, "⚠ Manual Review Recommended", 0, 1)
        pdf.set_text_color(0, 0, 0)  # Reset

    pdf.ln(5)

    # Sections
    for section in sorted(
        report_data.get("sections", []), key=lambda x: x.get("order", 0)
    ):
        # Section Title
        pdf.safe_set_font("DejaVu", "B", 14)
        pdf.set_fill_color(248, 250, 252)  # Slate 50
        pdf.cell(0, 10, f" {section.get('title')}", 0, 1, "L", fill=True)
        pdf.ln(2)

        # Section Content
        pdf.safe_set_font("DejaVu", "", 11)
        content = section.get("content", "")
        # Clean markdown bold
        content = content.replace("**", "")

        pdf.multi_cell(0, 7, content)
        pdf.ln(5)

    # Disclaimer
    pdf.safe_set_font("DejaVu", "I", 9)
    pdf.set_text_color(107, 114, 128)  # Gray 500
    pdf.ln(10)
    pdf.multi_cell(0, 5, report_data.get("disclaimer", ""))

    # Output to buffer or file
    if use_buffer:
        buffer = io.BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        return buffer
    else:
        pdf.output(str(output_path))
        return output_path


def get_pdf_bytes(report_data: Dict[str, Any]) -> bytes:
    """Helper to get PDF as bytes for API responses."""
    buffer = generate_pdf_report(report_data, use_buffer=True)
    return buffer.getvalue()


if __name__ == "__main__":
    # Test example
    test_report = {
        "report_id": "test123",
        "generated_at": "2026-03-03T12:00:00",
        "sections": [
            {
                "title": "Simulation Summary",
                "content": "• Peak Temperature: 412.3 K\n• Solver: MFEM + SUNDIALS",
                "order": 1,
            },
            {
                "title": "Key Metrics",
                "content": "• Max Stress: 125.8 MPa\n• ΔT: 122.9 K",
                "order": 2,
            },
        ],
        "disclaimer": "AI-generated interpretation.",
        "metadata": {},
    }

    buffer = generate_pdf_report(test_report)
    print(f"PDF generated: {len(buffer.getvalue())} bytes")
