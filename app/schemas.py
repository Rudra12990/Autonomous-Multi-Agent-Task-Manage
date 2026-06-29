from pydantic import BaseModel, Field
from typing import List, Optional

# FastAPI Request Schema — Make sure this name is exact!
class TaskRequest(BaseModel):
    raw_text: str

# Structured AI Output Models
class ResearchOutput(BaseModel):
    patch_version: str = Field(description="The exact version identifier of the software patch.")
    deployment_window: str = Field(description="The scheduled day and exact time of deployment.")
    technical_fixes: List[str] = Field(description="List of core technical changes, code refactors, or optimizations.")
    estimated_downtime_minutes: int = Field(description="The total estimated system downtime in minutes.")
    client_impacts: List[str] = Field(description="Potential side-effects, latency issues, or disruptions to clients.")
    pre_deployment_status: str = Field(description="Status of backup validation or verification checks.")

class AuditResult(BaseModel):
    status: str = Field(description="Must be exactly 'PASS' or 'FAIL'.")
    corrections: Optional[List[str]] = Field(default=None, description="If status is FAIL, an explicit list of required adjustments.")