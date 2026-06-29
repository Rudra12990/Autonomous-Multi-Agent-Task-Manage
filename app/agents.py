from typing import Type
from pydantic import BaseModel
from google.genai import types
from app.config import ai_client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class StructuredAgent:
    def __init__(self, name: str, system_instruction: str, response_schema: Type[BaseModel]):
        self.name = name
        self.system_instruction = system_instruction
        self.response_schema = response_schema

    # Automatically retry on API failures with exponential backoff (wait 2s, then 4s, then 8s...)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _call_gemini_with_retry(self, task_input: str):
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=task_input,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=self.response_schema
            )
        )
        return response.text

    async def run_task(self, task_input: str) -> BaseModel:
        # Running the retrying function
        raw_json = self._call_gemini_with_retry(task_input)
        return self.response_schema.model_validate_json(raw_json)