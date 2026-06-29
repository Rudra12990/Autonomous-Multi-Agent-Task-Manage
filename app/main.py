import uuid
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from app.schemas import TaskRequest, ResearchOutput, AuditResult
from app.agents import StructuredAgent
from app.config import supabase_client

# Initialize Enterprise FastAPI Framework
app = FastAPI(
    title="Production Multi-Agent Workspace Pipeline", 
    version="2.2.0",
    description="Asynchronous, type-safe multi-agent orchestration pipeline with automated self-healing loops."
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
            # Audit the current state of the extracted Pydantic object
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
            # Re-run the researcher agent using the targeted self-healing handle
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
            "user_query": raw_text,
            "research_output": research_data.model_dump(),     # Stored cleanly as native JSONB
            "critic_feedback": audit_data.model_dump() if audit_data else {"status": "UNKNOWN"},
            "final_output": final_output_payload
        }
        
        supabase_client.table("agent_logs").insert(log_entry).execute()
        
    except Exception as e:
        # Graceful background thread panic handling
        error_entry = {
            "user_query": raw_text,
            "final_output": f"Job {job_id} crashed during background processing: {str(e)}"
        }
        try:
            supabase_client.table("agent_logs").insert(error_entry).execute()
        except:
            pass

# --- High-Performance Web Service Route ---
@app.post("/api/v1/agent/execute", status_code=202)
async def execute_workspace_pipeline(payload: TaskRequest, background_tasks: BackgroundTasks):
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="Input payload text cannot be empty.")
    
    # Generate an isolated tracking ticket UUID for this execution flow
    job_id = str(uuid.uuid4())
    
    # Offload the entire heavy multi-agent sequence to the background thread pool
    background_tasks.add_task(background_pipeline_worker, job_id, payload.raw_text)
    
    # Instantly release the HTTP network connection back to the client
    return {
        "status": "accepted",
        "message": "Multi-agent processing pipeline initiated in background smoothly.",
        "job_id": job_id
    }