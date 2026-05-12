from __future__ import annotations

from typing import Any

from fpdf import FPDF


class PDFReportService:
    async def generate(self, report_spec: dict[str, Any]) -> bytes:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, report_spec.get("title", "Report"), ln=True, align="C")

        if report_spec.get("metadata"):
            pdf.set_font("Helvetica", "I", 10)
            for k, v in report_spec["metadata"].items():
                pdf.cell(0, 6, f"{k}: {v}", ln=True)
            pdf.ln(4)

        for section in report_spec.get("sections", []):
            if "heading" in section:
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, section["heading"], ln=True)
            if "content" in section:
                pdf.set_font("Helvetica", size=10)
                pdf.multi_cell(0, 5, section["content"])
            if "table" in section:
                pdf.set_font("Helvetica", size=9)
                with pdf.table() as table:
                    for row in section["table"]:
                        table_row = table.row()
                        for cell in row:
                            table_row.cell(str(cell))
            pdf.ln(2)

        if report_spec.get("include_manifest"):
            pdf.set_y(-30)
            pdf.set_font("Helvetica", "I", 8)
            pdf.cell(0, 10, f"Replay Manifest: {report_spec.get('replay_hash', 'N/A')}", align="C")

        return pdf.output()
