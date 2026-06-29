import os
from dotenv import load_dotenv
from google import genai
from supabase import create_client, Client

load_dotenv()

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

settings = Settings()

# Isolated Client Initializations
ai_client = genai.Client()
supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)