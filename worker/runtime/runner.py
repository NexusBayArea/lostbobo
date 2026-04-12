"""
Main execution loop for worker service
"""

import signal
import time
import uuid

from app.services.worker.runtime.bootstrap import preload_engine, preload_runtime
from app.services.worker.runtime.execute import execute_job
from app.services.worker.runtime.state import claim_job

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    print("\nShutdown signal received. Finishing current job...")
    shutdown_requested = True


def main():
    """Main worker execution loop"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Generate unique worker ID
    worker_id = f"worker-{uuid.uuid4()}"
    print(f"Starting worker {worker_id}")

    # Preload engine and runtime components
    print("Preloading components...")
    preload_engine()
    preload_runtime()
    print("Components preloaded. Starting job processing loop...")

    # Main processing loop
    while not shutdown_requested:
        try:
            # Claim a job from the queue
            job_data = claim_job(worker_id)

            if job_data is None:
                # No jobs available, sleep briefly before trying again
                time.sleep(1)
                continue

            job_id = job_data["id"]

            print(f"Claimed job {job_id}")

            # Execute the job
            result = execute_job(job_data)

            # Update job status based on execution result
            if result["success"]:
                print(f"Job {job_id} completed successfully")
                # Attempt count is already incremented in execute_job via update_job_status
            else:
                print(f"Job {job_id} failed: {result.get('error', 'Unknown error')}")

            # Small delay between jobs to prevent tight loop
            time.sleep(0.1)
        except Exception as e:
            print(f"Error in worker loop: {e}")
            time.sleep(5)  # Longer sleep on unexpected errors

    print(f"Worker {worker_id} shutting down gracefully...")


if __name__ == "__main__":
    main()
