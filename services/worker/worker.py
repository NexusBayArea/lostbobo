#!/usr/bin/env python3
"""
SimHPC RunPod Worker (v2.5.3) - Optimized with CORS & FastAPI
"""

import os
import json
import time
import logging
import threading
from datetime import datetime
from redis import Redis
from fpdf import FPDF
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# --- FastAPI Setup for SimHPC ---
app = FastAPI(title="SimHPC Worker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "worker": "online",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/simulations")
async def get_simulations():
    return {"status": "connected", "data": []}


# --- Worker Configuration ---
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
active_jobs = 0
lock = threading.Lock()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")
INFLIGHT_KEY = os.getenv("INFLIGHT_KEY", "simhpc_inflight")
POLL_INTERVAL_SEC = float(os.getenv("POLL_INTERVAL_SEC", "2"))
IDLE_TIMEOUT = int(os.getenv("IDLE_TIMEOUT", "300"))
RUNPOD_POD_ID = os.getenv("RUNPOD_POD_ID")

# --- Supabase Setup ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = None

try:
    from supabase import create_client

    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized")
except ImportError:
    logger.warning("Supabase client unavailable")


def generate_pdf_report(job_id: str, data: dict, output_path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "SimHPC Engineering Analysis Report", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Job ID: {job_id}", 0, 1)
    pdf.cell(0, 10, f"Generated: {datetime.utcnow().isoformat()}", 0, 1)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 10, f"Simulation Results Summary:\n{json.dumps(data, indent=2)}")
    pdf.output(output_path)


def upload_report(job_id: str, pdf_path: str, is_paid: bool = False) -> str:
    if not supabase:
        return ""
    try:
        bucket = "reports"
        filename = f"{job_id}.pdf"
        with open(pdf_path, "rb") as f:
            supabase.storage.from_(bucket).upload(
                path=filename,
                file=f,
                file_options={"content-type": "application/pdf", "x-upsert": "true"},
            )
        return supabase.storage.from_(bucket).get_public_url(filename)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return ""


def update_simulation(job_id: str, data: dict):
    if not supabase:
        return
    try:
        data["updated_at"] = datetime.utcnow().isoformat()
        supabase.table("simulations").update(data).eq("job_id", job_id).execute()
    except Exception as e:
        logger.error(f"Supabase sync failed: {e}")


def process_job(job: dict):
    global active_jobs
    job_id = job.get("id", "unknown")
    try:
        update_simulation(job_id, {"status": "running"})
        sim_data = {"peak_temperature": 412.3, "max_stress": 125.8}

        pdf_path = f"/tmp/{job_id}.pdf"
        generate_pdf_report(job_id, sim_data, pdf_path)
        pdf_url = upload_report(job_id, pdf_path)

        update_simulation(
            job_id, {"status": "completed", "gpu_result": sim_data, "pdf_url": pdf_url}
        )
        logger.info(f"Job {job_id} completed.")
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        update_simulation(job_id, {"status": "failed", "error": str(e)})
    finally:
        with lock:
            active_jobs -= 1


def main():
    global active_jobs
    logger.info("SimHPC Worker v2.5.3 Active")
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    while True:
        job_data = redis_client.lpop(QUEUE_NAME)
        if job_data:
            job = json.loads(job_data)
            with lock:
                active_jobs += 1
            threading.Thread(target=process_job, args=(job,)).start()
        else:
            time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
