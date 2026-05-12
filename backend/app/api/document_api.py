from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/document", tags=["document"])


def get_kernel(request):
    return request.app.state.kernel


def get_tenant_id(request=None):
    if request is None:
        return "default"
    return request.headers.get("X-Tenant-ID", "default")


KernelDep = Depends(get_kernel)


class CertificateRequest(BaseModel):
    certificate_hash: str
    include_manifest: bool = True


@router.post("/pdf")
async def generate_pdf_report(report_spec: dict, kernel=KernelDep):
    try:
        pdf_bytes = await kernel.capabilities.invoke("document.generate_pdf", report_spec)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=report.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/ingest_pdf")
async def ingest_pdf(file: UploadFile = File(...), kernel=KernelDep):  # noqa: B008
    tenant_id = get_tenant_id(None)
    file_bytes = await file.read()
    count = await kernel.capabilities.invoke(
        "memory.ingest_pdf",
        {
            "file_bytes": file_bytes,
            "tenant_id": tenant_id,
            "plugin_name": "ui",
        },
    )
    return {"status": "success", "chunks_created": count}


@router.post("/download")
async def download_generated_pdf(report_spec: dict, kernel=KernelDep):
    try:
        pdf_bytes = await kernel.capabilities.invoke("document.generate_pdf", report_spec)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=report.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/certificate/download")
async def download_certificate(req: CertificateRequest, kernel=KernelDep):
    pdf_bytes = await kernel.capabilities.invoke(
        "document.generate_certificate",
        {
            "certificate_hash": req.certificate_hash,
            "include_manifest": req.include_manifest,
        },
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=simhpc_certificate_{req.certificate_hash}.pdf"},
    )
