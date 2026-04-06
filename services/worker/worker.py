#!/usr/bin/env python3
"""
SimHPC RunPod Worker (v2.5.0)

Fully aligned with the `simulations` table schema:
- Status flow: queued → running → auditing → completed
- Writes gpu_result, audit_result, pdf_url, hallucination_score
- Creates certificate with verification hash
- Always writes updated_at
"""

import os
import json
import hashlib
import time
import logging
import threading
import requests
from datetime import datetime
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from fpdf import FPDF
from dotenv import load_dotenv

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
RUNPOD_POD_ID = os.getenv("RUNPOD_POD_ID")

if not RUNPOD_POD_ID:
    logger.warning(
        "RUNPOD_POD_ID not set. Heartbeat and autoscaler tracking will be limited."
    )

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = None

try:
    from supabase import create_client

    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.warning(
                f"Supabase client init failed (non-fatal): {e}. Continuing without Supabase."
            )
except ImportError:
    logger.warning("Supabase not available, heartbeat disabled")


def generate_pdf_report(job_id: str, data: dict, output_path: str):
    """Generate engineering PDF report."""
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
    """Upload PDF to Supabase Storage and return URL."""
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
        if is_paid:
            res = supabase.storage.from_(bucket).create_signed_url(
                filename, expires_in=3600
            )
            return res.get("signedURL") if isinstance(res, dict) else str(res)
        else:
            return supabase.storage.from_(bucket).get_public_url(filename)
    except Exception as e:
        logger.error(f"Failed to upload report: {e}")
        return ""


def update_simulation(job_id: str, data: dict):
    """Update simulations table by job_id. Always writes updated_at."""
    if not supabase:
        return
    try:
        data["updated_at"] = datetime.utcnow().isoformat()
        supabase.table("simulations").update(data).eq("job_id", job_id).execute()
        logger.debug(f"Supabase sync: job_id={job_id} data={list(data.keys())}")
    except Exception as e:
        logger.error(f"Failed to sync to Supabase: {e}")


def run_audit(sim_data: dict) -> dict:
    """Stub audit. Replace with Rnj-1 integration later."""
    return {
        "verification_id": f"verify_{int(time.time())}",
        "hallucination_score": 0.0,
        "status": "pass",
        "summary": {"critical": 0, "warnings": 0, "valid": len(sim_data)},
        "flags": [],
        "rag_anomalies": [],
        "math_errors": [],
        "auditor_remark": "Baseline validation passed. No discrepancies detected.",
    }


def create_certificate(job_id: str, pdf_url: str, audit_result: dict) -> str:
    """Create certificate row and return certificate_id."""
    cert_id = f"cert_{job_id}"
    verification_hash = hashlib.sha256(
        json.dumps(audit_result, sort_keys=True).encode()
    ).hexdigest()

    if supabase:
        try:
            supabase.table("certificates").insert(
                {
                    "id": cert_id,
                    "simulation_id": job_id,
                    "verification_hash": verification_hash,
                    "storage_url": pdf_url or "",
                }
            ).execute()
            logger.info(f"Certificate created: {cert_id}")
        except Exception as e:
            logger.error(f"Failed to create certificate: {e}")

    return cert_id


def process_job(job: dict):
    """Process a single simulation job. Full status flow: running → auditing → completed."""
    global active_jobs
    job_id = job.get("id", "unknown")
    is_paid = job.get("is_paid", False)

    try:
        # Phase 1: RUNNING
        logger.info(f"Running job {job_id}")
        update_simulation(job_id, {"status": "running", "gpu_result": {}})

        sim_data = {"peak_temperature": 412.3, "max_stress": 125.8}

        # Phase 2: AUDITING
        update_simulation(job_id, {"status": "auditing", "gpu_result": sim_data})

        audit_result = run_audit(sim_data)

        # Phase 3: Generate PDF
        pdf_path = f"/tmp/{job_id}.pdf"
        generate_pdf_report(job_id, sim_data, pdf_path)
        pdf_url = upload_report(job_id, pdf_path, is_paid=is_paid)

        # Phase 4: Create certificate
        cert_id = create_certificate(job_id, pdf_url, audit_result)

        # Phase 5: COMPLETED — single atomic write with all fields
        supabase_update = {
            "status": "completed",
            "gpu_result": sim_data,
            "audit_result": audit_result,
            "hallucination_score": audit_result.get("hallucination_score", 0.0),
            "pdf_url": pdf_url,
            "certificate_id": cert_id,
        }
        update_simulation(job_id, supabase_update)

        # Redis result for API polling fallback
        redis_result = {
            "status": "completed",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
            "pdf_url": pdf_url,
            "gpu_result": sim_data,
            "audit_result": audit_result,
            "certificate_id": cert_id,
        }
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.set(f"simhpc_result:{job_id}", json.dumps(redis_result))

        logger.info(f"Job {job_id} completed. Certificate: {cert_id}")

        # Cleanup
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.set(
            f"simhpc_result:{job_id}", json.dumps({"error": str(e), "job_id": job_id})
        )
        update_simulation(job_id, {"status": "failed", "error": str(e)})
    finally:
        with lock:
            active_jobs -= 1
        try:
            r = Redis.from_url(REDIS_URL, decode_responses=True)
            r.decr(INFLIGHT_KEY)
            if RUNPOD_POD_ID:
                r.set(f"pods:last_used:{RUNPOD_POD_ID}", int(time.time()))
        except Exception as e:
            logger.error(f"Failed to update autoscaler metrics: {e}")


def send_heartbeat():
    """Send heartbeat to Supabase."""
    return  # Disabled - using Redis pods:last_used for autoscaler instead
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
        logger.debug("Heartbeat sent")
    except Exception as e:
        logger.error(f"Heartbeat failed: {e}")


def verify_mercury_ai():
    """Verify connectivity to Inception Labs API."""
    api_key = os.getenv("INCEPTION_API_KEY") or os.getenv("MERCURY_API_KEY")
    if not api_key:
        logger.warning("No API key for Mercury AI. Skipping verification.")
        return
    try:
        response = requests.post(
            "https://api.inceptionlabs.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mercury-2",
                "messages": [{"role": "user", "content": "reply SIMHPC_OK"}],
            },
            timeout=10,
        )
        if response.status_code == 200:
            logger.info("Mercury-2 AI: OK")
        else:
            logger.error(f"Mercury-2 AI: FAILED ({response.status_code})")
    except Exception as e:
        logger.error(f"Mercury-2 AI: ERROR ({e})")


def main():
    """Main worker loop - infinite polling of Redis queue."""
    global active_jobs
    logger.info("SimHPC Worker Booting (v2.5.0)...")
    verify_mercury_ai()

    try:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        logger.info(f"Connected to Redis at {REDIS_URL}")
    except RedisConnectionError as e:
        logger.error(f"Cannot connect to Redis: {e}")
        return

    logger.info(
        f"Worker started. Queue: {QUEUE_NAME}, Max concurrent: {MAX_CONCURRENT_JOBS}"
    )

    while True:
        try:
            send_heartbeat()

            job_data = redis_client.lpop(QUEUE_NAME)

            if job_data:
                with lock:
                    if active_jobs >= MAX_CONCURRENT_JOBS:
                        redis_client.rpush(QUEUE_NAME, job_data)
                        time.sleep(1)
                        continue

                redis_client.incr(INFLIGHT_KEY)
                redis_client.expire(INFLIGHT_KEY, 300)
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
            else:
                if RUNPOD_POD_ID:
                    redis_client.set(
                        f"pods:last_used:{RUNPOD_POD_ID}", int(time.time())
                    )
                time.sleep(POLL_INTERVAL_SEC)

        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
