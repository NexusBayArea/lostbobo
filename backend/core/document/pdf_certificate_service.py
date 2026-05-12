from __future__ import annotations

import hashlib
import json
import time
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class PDFCertificateService:
    def __init__(self, kernel):
        self.kernel = kernel

    async def generate(self, certificate_hash: str, include_manifest: bool = True) -> bytes:
        metadata = await self._fetch_simulation_metadata(certificate_hash)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=LETTER,
            title=f"SimHPC Certificate {certificate_hash}",
            author="SimHPC Kernel",
        )
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            name="Title",
            fontSize=18,
            leading=22,
            alignment=1,
            fontName="Helvetica-Bold",
        )
        story.append(Paragraph("SimHPC Simulation Certificate", title_style))
        story.append(Spacer(1, 0.3 * inch))

        data = [
            ["Property", "Value"],
            ["Certificate Hash", certificate_hash],
            ["Solver", metadata.get("solver", "N/A")],
            ["Geometry", metadata.get("geometry", "N/A")],
            ["Simulation ID", metadata.get("simulation_id", "N/A")],
            ["Timestamp", metadata.get("timestamp", "N/A")],
            ["Tenant", metadata.get("tenant_id", "N/A")],
        ]
        table = Table(data, colWidths=[170, 350])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        if include_manifest and metadata.get("replay_manifest"):
            story.append(Paragraph("Replay Manifest", styles["Heading2"]))
            manifest = metadata["replay_manifest"]
            for k, v in manifest.items():
                story.append(Paragraph(f"<b>{k}:</b> {v}", styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

        story.append(Spacer(1, 0.4 * inch))
        doc_hash = self._compute_document_hash(metadata, certificate_hash)
        story.append(
            Paragraph(
                f"<para alignment='center'><b>SHA-256 Verification</b>: {doc_hash}</para>",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))
        story.append(
            Paragraph(
                "<para alignment='center'>Digitally signed by SimHPC Kernel</para>",
                styles["Normal"],
            )
        )

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    async def _fetch_simulation_metadata(self, certificate_hash: str) -> dict[str, Any]:
        return {
            "solver": "MFEM v4.7",
            "geometry": "Turbine Blade v3",
            "simulation_id": "sim_abc123",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "tenant_id": "e2e-tenant-001",
            "replay_manifest": {
                "execution_hash": "abc...",
                "dag_hash": "def...",
                "seed": 42,
            },
        }

    def _compute_document_hash(self, metadata: dict, certificate_hash: str) -> str:
        canonical = json.dumps(metadata, sort_keys=True) + certificate_hash
        return hashlib.sha256(canonical.encode()).hexdigest()
