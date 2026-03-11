import runpod
import os
import time
from mercury import MercuryModel
from reportlab.pdfgen import canvas
from supabase import create_client, Client

# ─── Preload Model (Worker Boot) ──────────────────────────────────────────────
print("Loading Mercury model...")
model = MercuryModel()
print("Mercury ready")

# ─── Supabase Integration ─────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_pdf(text, job_id):
    """Generates a SimHPC PDF result and returns the local path."""
    path = f"/tmp/{job_id}.pdf"
    
    c = canvas.Canvas(path)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "SimHPC Engineering Report")
    
    c.setFont("Helvetica", 10)
    c.drawString(100, 730, f"Job ID: {job_id}")
    c.drawString(100, 715, f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    c.line(100, 705, 500, 705)
    
    # Simple text wrapping for the Mercury result
    text_object = c.beginText(100, 680)
    text_object.setFont("Helvetica", 11)
    text_object.setLeading(14)
    
    lines = text.split('\n')
    for line in lines:
        # Very basic manual wrapping for the demo
        if len(line) > 80:
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) < 80:
                    current_line += word + " "
                else:
                    text_object.textLine(current_line)
                    current_line = word + " "
            text_object.textLine(current_line)
        else:
            text_object.textLine(line)
            
    c.drawText(text_object)
    c.save()
    return path

def handler(event):
    """Main RunPod Serverless Handler."""
    inputs = event["input"]
    job_id = event["id"]
    
    prompt = inputs.get("prompt", "Run default simulation")
    
    # 1. Mercury Inference
    print(f"Running Mercury for prompt: {prompt}")
    result = model.run(prompt)
    
    # 2. PDF Generation
    pdf_local_path = generate_pdf(result, job_id)
    
    # 3. Optional: Direct Supabase Upload from Worker
    pdf_url = None
    if supabase:
        try:
            with open(pdf_local_path, "rb") as f:
                storage_path = f"results/{job_id}.pdf"
                supabase.storage.from_("results").upload(
                    storage_path, 
                    f, 
                    {"content-type": "application/pdf"}
                )
                pdf_url = supabase.storage.from_("results").get_public_url(storage_path)
        except Exception as e:
            print(f"Upload failed: {str(e)}")

    return {
        "status": "complete",
        "result": result,
        "pdf_url": pdf_url,
        "job_id": job_id
    }

# Start the RunPod Serverless Worker
runpod.serverless.start({"handler": handler})
