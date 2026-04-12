import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class WorkflowService:
    def __init__(self, supabase_client, redis_client, enqueue_job_fn):
        self.supabase = supabase_client
        self.redis = redis_client
        self.enqueue_job = enqueue_job_fn

    async def create_workflow(self, user_id: str, name: str, steps: List[Dict[str, Any]], context: Dict[str, Any] = None) -> str:
        workflow_id = str(uuid.uuid4())
        
        # Insert workflow
        self.supabase.table("workflows").insert({
            "id": workflow_id,
            "user_id": user_id,
            "name": name,
            "total_steps": len(steps),
            "context": context or {},
            "status": "active"
        }).execute()

        # Insert steps
        for i, step in enumerate(steps):
            self.supabase.table("workflow_steps").insert({
                "workflow_id": workflow_id,
                "step_number": i + 1,
                "name": step.get("name"),
                "status": "pending"
            }).execute()

        # Start first step
        await self.run_step(workflow_id, 1)
        
        return workflow_id

    async def run_step(self, workflow_id: str, step_number: int):
        # Update workflow current step
        self.supabase.table("workflows").update({"current_step": step_number, "updated_at": datetime.utcnow().isoformat()}).eq("id", workflow_id).execute()
        
        # Get step details
        res = self.supabase.table("workflow_steps").select("*").eq("workflow_id", workflow_id).eq("step_number", step_number).single().execute()
        step = res.data
        
        # Create job for this step
        job_id = f"wf-{workflow_id}-{step_number}"
        
        # In a real system, we'd have logic to generate input_params based on previous step results
        # For now, let's assume the step name determines the action
        
        job_data = {
            "id": job_id,
            "workflow_id": workflow_id,
            "step_number": step_number,
            "input_params": {"step_name": step["name"]},
            "status": "queued"
        }
        
        # Link job to step
        self.supabase.table("workflow_steps").update({
            "status": "running", 
            "job_id": job_id,
            "started_at": datetime.utcnow().isoformat()
        }).eq("id", step["id"]).execute()
        
        # Enqueue
        self.enqueue_job(job_data)

    async def complete_step(self, workflow_id: str, step_number: int, result: Dict[str, Any]):
        # Mark step as completed
        self.supabase.table("workflow_steps").update({
            "status": "completed",
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("workflow_id", workflow_id).eq("step_number", step_number).execute()
        
        # Check if more steps
        res = self.supabase.table("workflows").select("*").eq("id", workflow_id).single().execute()
        workflow = res.data
        
        if step_number < workflow["total_steps"]:
            # Run next step
            await self.run_step(workflow_id, step_number + 1)
        else:
            # Workflow complete
            self.supabase.table("workflows").update({
                "status": "completed", 
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", workflow_id).execute()
