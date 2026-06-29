import uuid
import json
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.schemas import TaskRequest, ResearchOutput, AuditResult
from app.agents import StructuredAgent
from app.config import supabase_client

# Initialize Enterprise FastAPI Framework
app = FastAPI(
    title="OpsMind Production Hub", 
    version="3.0.0",
    description="Unified multi-agent logging, audit, and static web distribution server."
)

# Instantiate production-grade structured agents with strict schemas
researcher = StructuredAgent(
    name="Domain Researcher",
    system_instruction=(
        "Extract core technical milestones, system parameters, dates, patches, "
        "downtime windows, and versioning strings from raw unstructured developer text logs."
    ),
    response_schema=ResearchOutput
)

critic = StructuredAgent(
    name="Compliance Critic",
    system_instruction=(
        "You are a strict technical compliance inspector. Audit the incoming data objects. "
        "Set your status to PASS only if patch versions are fully specified, downtime is explicit, "
        "and client impacts or fixes are populated. If any field is empty, default, or uninformative, "
        "set status to FAIL and provide an explicit list of required corrections in the corrections array."
    ),
    response_schema=AuditResult
)

# --- Asynchronous Self-Healing Background Worker Pool ---
async def background_pipeline_worker(job_id: str, raw_text: str):
    try:
        # Step 1: Initial Structured Extraction
        research_data: ResearchOutput = await researcher.run_task(raw_text)
        
        max_correction_attempts = 3
        audit_data = None
        
        # Step 2: Fault-Tolerant Reflection & Correction Feedback Loop
        for attempt in range(1, max_correction_attempts + 1):
            audit_data: AuditResult = await critic.run_task(research_data.model_dump_json())
            
            # If the inspector passes the data structure, break out immediately
            if audit_data.status == "PASS":
                break
                
            # If it fails, compile the explicit errors and re-route to the agent workforce
            correction_prompt = (
                f"Your previous data extraction failed strict compliance audit rules. Please correct the fields "
                f"based on this explicit feedback from the inspector:\n{json.dumps(audit_data.corrections)}\n\n"
                f"ORIGINAL RAW UNSTRUCTURED TEXT:\n{raw_text}"
            )
            research_data = await researcher.run_task(correction_prompt)

        # Compile final structural payload based on loop outcome
        if audit_data and audit_data.status == "PASS":
            final_output_payload = research_data.model_dump_json()
        else:
            final_output_payload = (
                f"Pipeline Terminated: Failed compliance after {max_correction_attempts} attempts. "
                f"Unresolved issues: {json.dumps(audit_data.corrections if audit_data else [])}"
            )
        
        # ====== Log Normalized Safe Data to Supabase ======
        log_entry = {
            "id": job_id,                                      # Syncing using tracking key explicitly
            "user_query": raw_text,
            "research_output": research_data.model_dump(),     # Stored cleanly as native JSONB
            "critic_feedback": audit_data.model_dump() if audit_data else {"status": "UNKNOWN"},
            "final_output": final_output_payload
        }
        
        supabase_client.table("agent_logs").insert(log_entry).execute()
        
    except Exception as e:
        # Graceful background thread panic handling fallback
        error_entry = {
            "id": job_id,
            "user_query": raw_text,
            "final_output": f"Job crashed during background processing: {str(e)}"
        }
        try:
            supabase_client.table("agent_logs").insert(error_entry).execute()
        except:
            pass

# --- High-Performance Web Service Routes ---

@app.post("/api/v1/agent/execute", status_code=202)
async def execute_workspace_pipeline(payload: TaskRequest, background_tasks: BackgroundTasks):
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="Input payload text cannot be empty.")
    
    # Generate an isolated tracking ticket UUID for this execution flow
    job_id = str(uuid.uuid4())
    
    # Offload the entire heavy multi-agent sequence to the background thread pool
    background_tasks.add_task(background_pipeline_worker, job_id, payload.raw_text)
    
    return {
        "status": "accepted",
        "message": "Multi-agent processing pipeline initiated in background smoothly.",
        "job_id": job_id
    }

@app.get("/api/v1/agent/status/{job_id}")
async def get_job_status(job_id: str):
    try:
        # Look inside your database ledger for the matching tracking key row entry
        response = supabase_client.table("agent_logs").select("*").eq("id", job_id).execute()
        if response.data:
            record = response.data[0]
            return {
                "status": "completed",
                "research_output": record.get("research_output"),
                "critic_feedback": record.get("critic_feedback"),
                "final_output": record.get("final_output")
            }
    except Exception:
        pass
        
    return {"status": "processing"}

# --- Static Frontend App Distribution Web Assets ---

# Mount the static web folder directory mapping parameters
app.mount("/static", StaticFiles(directory="static"), name="static")

# Expose the core index.html file right at the root landing domain route
@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join("static", "index.html"))