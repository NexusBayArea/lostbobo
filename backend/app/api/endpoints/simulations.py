from fastapi import APIRouter, HTTPException
from typing import Any
from backend.app.core.supabase import supabase
from backend.app.services.mercury import mercury_ai

router = APIRouter()

GUIDANCE_PROMPT_TEMPLATE = """
Analyze the following simulation results for Job ID: {job_id}.
Type: {sim_type}
Material: {material_name}
Final Progress: {progress}%
Thermal Drift: {thermal_drift}
Pressure Spike: {pressure_spike}
Status: {status}

Provide a concise technical summary and recommendation for the next iteration.
"""

@router.get("/")
async def list_simulations(user_id: str):
    query = supabase.table("simulation_history").select(
        "id, job_id, status, progress, certificate_hash, credit_cost, last_ping, created_at"
    )
    
    if user_id != 'ALL_FLEET':
        query = query.eq("user_id", user_id)
        
    res = query.order("created_at", desc=True).execute()
    return res.data

@router.post("/generate-report/{job_id}", tags=["Mercury AI"])
async def generate_guidance_report(job_id: str) -> Any:
    try:
        res = supabase.table("simulation_history").select("*").eq("job_id", job_id).single().execute()
        sim_data = res.data
        
        if not sim_data:
            raise HTTPException(status_code=404, detail="Simulation record not found")

        results_blob = sim_data.get('results', {})
        
        prompt = GUIDANCE_PROMPT_TEMPLATE.format(
            job_id=sim_data['job_id'],
            sim_type=sim_data.get('sim_type', 'N/A'),
            material_name=results_blob.get('material', 'Standard Alloy'),
            progress=sim_data.get('progress', 0),
            thermal_drift=sim_data.get('thermal_drift', 0),
            pressure_spike=sim_data.get('pressure_spike', False),
            status=sim_data.get('status', 'unknown')
        )

        report_content = await mercury_ai.generate(prompt)
        
        updated_results = {**results_blob, "ai_report": report_content}
        
        supabase.table("simulation_history").update({
            "results": updated_results
        }).eq("job_id", job_id).execute()

        return {"job_id": job_id, "report": report_content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
