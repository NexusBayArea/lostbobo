#!/usr/bin/env python3
"""
SimHPC RunPod Worker
RunPod Pod worker that processes simulation jobs from Redis queue.

Key features:
- Infinite loop (while True)
- Polls Redis queue for jobs
- Concurrent job processing with MAX_CONCURRENT_JOBS limit
- Heartbeat to Supabase for health monitoring
- Updates simulation_history table for real-time dashboard sync
"""

import os
import json
import time
import logging
import threading
from datetime import datetime
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from fpdf import FPDF
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
RUNPOD_POD_ID = os.getenv("RUNPOD_POD_ID", "x613fv0zoyvtx9")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = None

try:
    from supabase import create_client

    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized")
except ImportError:
    logger.warning("Supabase not available, heartbeat disabled")


def generate_pdf_report(job_id: str, data: dict, output_path: str):
    """Minimal PDF generation for engineering reports."""
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
    logger.info(f"PDF report generated at {output_path}")


def upload_report(job_id: str, pdf_path: str, is_paid: bool = False) -> str:
    """Uploads PDF to Supabase Storage and returns URL."""
    if not supabase:
        return ""
        
    try:
        bucket = "reports"
        filename = f"{job_id}.pdf"
        
        with open(pdf_path, "rb") as f:
            supabase.storage.from_(bucket).upload(
                path=filename,
                file=f,
                file_options={"content-type": "application/pdf", "x-upsert": "true"}
            )
            
        if is_paid:
            # Signed URL (1 hour)
            res = supabase.storage.from_(bucket).create_signed_url(filename, expires_in=3600)
            return res.get("signedURL") if isinstance(res, dict) else str(res)
        else:
            # Public URL
            return supabase.storage.from_(bucket).get_public_url(filename)
            
    except Exception as e:
        logger.error(f"Failed to upload report: {e}")
        return ""


def update_job_status(job_id: str, status: str, result: dict = None):
    """Updates Supabase so the Frontend Dashboard reflects reality in real-time."""
    if not supabase:
        return
    try:
        data = {"status": status}
        if result:
            data["result_summary"] = result
            # Use pdf_url as canonical report link
            data["report_url"] = result.get("pdf_url") or result.get("pdf_link")
        supabase.table("simulation_history").update(data).eq("job_id", job_id).execute()
        logger.debug(f"Supabase status sync: {job_id} -> {status}")
    except Exception as e:
        logger.error(f"Failed to sync status to Supabase: {e}")


def process_job(job: dict):
    """Process a single simulation job."""
    global active_jobs
    job_id = job.get("id", "unknown")
    is_paid = job.get("is_paid", False)

    try:
        logger.info(f"Running job {job_id}")
        update_job_status(job_id, "running")

        # Simulation logic (stub)
        sim_data = {"peak_temperature": 412.3, "max_stress": 125.8}
        
        # 1. Generate PDF
        pdf_path = f"/tmp/{job_id}.pdf"
        generate_pdf_report(job_id, sim_data, pdf_path)
        
        # 2. Upload and get URL
        pdf_url = upload_report(job_id, pdf_path, is_paid=is_paid)

        result = {
            "status": "completed",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
            "pdf_url": pdf_url,
            "data": sim_data,
        }

        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.set(f"simhpc_result:{job_id}", json.dumps(result))
        update_job_status(job_id, "completed", result)
        logger.info(f"Done {job_id}")

        # Cleanup
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.set(
            f"simhpc_result:{job_id}", json.dumps({"error": str(e), "job_id": job_id})
        )
        update_job_status(job_id, "failed", {"error": str(e)})
    finally:
        with lock:
            active_jobs -= 1
        
        # Tracking for autoscaler
        try:
            r = Redis.from_url(REDIS_URL, decode_responses=True)
            r.decr(INFLIGHT_KEY)
            if RUNPOD_POD_ID:
                r.set(f"pods:last_used:{RUNPOD_POD_ID}", int(time.time()))
        except Exception as e:
            logger.error(f"Failed to update autoscaler metrics: {e}")


def send_heartbeat():
    """Send heartbeat to Supabase."""
    if not supabase:
        return
    try:
        supabase.table("worker_heartbeat").upsert(
            {
                "worker_id": RUNPOD_POD_ID,
                "status": "online",
                "last_ping": datetime.utcnow().isoformat(),
            }
        ).execute()
        logger.debug("Heartbeat sent to Supabase")
    except Exception as e:
        logger.error(f"Heartbeat failed: {e}")


def verify_mercury_ai():
    """Verify connectivity to Inception Labs API (Mercury-2)."""
    api_key = os.getenv("INCEPTION_API_KEY") or os.getenv("MERCURY_API_KEY")
    if not api_key:
        logger.warning("No API key found for Inception/Mercury AI. Skipping verification.")
        return

    logger.info(f"Verifying Mercury-2 AI connectivity...")
    try:
        response = requests.post(
            "https://api.inceptionlabs.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mercury-2",
                "messages": [
                    {"role": "user", "content": "What is the meaning of life?"}
                ]
            },
            timeout=10
        )
        if response.status_code == 200:
            logger.info("Mercury-2 AI verification: ✓ SUCCESS")
        else:
            logger.error(f"Mercury-2 AI verification: ✗ FAILED (Status: {response.status_code})")
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Mercury-2 AI verification: ✗ ERROR ({str(e)})")


def main():
    """Main worker loop - infinite polling of Redis queue."""
    global active_jobs
    logger.info("SimHPC Worker Booting...")

    # Verify AI Connectivity
    verify_mercury_ai()

    try:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        logger.info(f"Connected to Redis at {REDIS_URL}")
    except RedisConnectionError as e:
        logger.error(f"Cannot connect to Redis: {e}")
        return

    logger.info(f"Worker started. Waiting for jobs...")
    logger.info(f"Queue: {QUEUE_NAME}, Max concurrent jobs: {MAX_CONCURRENT_JOBS}")

    last_active = time.time()

    while True:
        try:
            with lock:
                if active_jobs >= MAX_CONCURRENT_JOBS:
                    time.sleep(1)
                    continue

            job_data = redis_client.lpop(QUEUE_NAME)

            if job_data:
                last_active = time.time()
                # Tracking for autoscaler
                redis_client.incr(INFLIGHT_KEY)
                try:
                    job = json.loads(job_data)
                    with lock:
                        active_jobs += 1
                    threading.Thread(target=process_job, args=(job,)).start()
                    logger.info(
                        f"Started job {job.get('id', 'unknown')} (active: {active_jobs})"
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode job: {e}")
                    with lock:
                        active_jobs -= 1
                    redis_client.decr(INFLIGHT_KEY)
                send_heartbeat()
            else:
                idle_time = time.time() - last_active
                if idle_time > IDLE_TIMEOUT:
                    logger.info(f"Idle for {idle_time}s > {IDLE_TIMEOUT}s threshold")
                
                # Ensure autoscaler knows this pod is idle but active
                if RUNPOD_POD_ID:
                    redis_client.set(f"pods:last_used:{RUNPOD_POD_ID}", int(time.time()))
                
                send_heartbeat()
                time.sleep(POLL_INTERVAL_SEC)

        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
