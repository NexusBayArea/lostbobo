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


def process_job(job):
    # simulate work (replace with real sim)
    job_id = job.get("id")
    for i in range(1, 6):
        job["status"] = "running"
        job["progress"] = i * 20
        job["updated_at"] = int(time.time())

        # Sync back to Redis for API status polling
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.set(f"job:{job_id}", json.dumps(job))

        # Sync to Supabase for Dashboard realtime
        update_simulation(job_id, {
            "status": "running",
            "progress": job["progress"]
        })
        time.sleep(2)

    job["status"] = "completed"
    job["result"] = {"message": "simulation complete"}
    job["updated_at"] = int(time.time())

    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.set(f"job:{job_id}", json.dumps(job))

    # Final sync to Supabase
    update_simulation(job_id, {
        "status": "completed",
        "gpu_result": job["result"]
    })


def main():
    logger.info("SimHPC Worker v2.5.5 Unified Active")
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

    while True:
        # Use BRPOP for blocking pull as requested
        item = redis_client.brpop(QUEUE_NAME, timeout=5)

        if not item:
            continue

        job_id = item[1]

        # Check if job_id is just a string or JSON (patch expects job_id)
        try:
            # Try parsing as JSON first in case it's a full job object
            job = json.loads(job_id)
            actual_job_id = job.get("id")
        except:
            # Fallback: it's just a raw ID string
            actual_job_id = job_id
            job_data = redis_client.get(f"job:{actual_job_id}")
            if not job_data:
                logger.warning(f"Job data missing for ID: {actual_job_id}")
                continue
            job = json.loads(job_data)

        try:
            logger.info(f"Processing job: {actual_job_id}")
            process_job(job)
        except Exception as e:
            logger.error(f"Job {actual_job_id} failed: {e}")
            job["status"] = "failed"
            job["error"] = str(e)
            job["updated_at"] = int(time.time())
            job["retries"] = job.get("retries", 0) + 1
            redis_client.set(f"job:{actual_job_id}", json.dumps(job))
            update_simulation(actual_job_id, {"status": "failed", "error": str(e)})

if __name__ == "__main__":
    main()
