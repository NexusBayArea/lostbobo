"""
Compute logic wrapper for worker execution
"""

import time
import traceback
from typing import Any, Dict

from app.services.worker.runtime.state import update_job_status


def execute_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the compute logic for a job
    This is where the actual simulation/workload would run
    """
    job_id = job_data["id"]
    payload = job_data["payload"]

    try:
        # Update status to running
        update_job_status(job_id, "running")

        # Simulate work based on payload
        # In a real implementation, this would call your simulation engine
        result = simulate_workload(payload)

        # Mark job as completed
        update_job_status(job_id, "done", result=result)

        return {"success": True, "result": result, "job_id": job_id}

    except Exception as e:
        # Capture error details
        error_msg = str(e)
        error_trace = traceback.format_exc()

        # Update job status to failed
        update_job_status(job_id, "failed", error=error_msg)

        return {
            "success": False,
            "error": error_msg,
            "traceback": error_trace,
            "job_id": job_id,
        }


def simulate_workload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate workload execution
    Replace this with actual simulation logic
    """
    # Simulate some processing time
    time.sleep(2)  # Simulate 2 seconds of work

    # Return mock result based on payload
    return {
        "status": "completed",
        "input_received": payload,
        "timestamp": time.time(),
        "computed_result": f"Processed {len(str(payload))} bytes of input data",
    }
