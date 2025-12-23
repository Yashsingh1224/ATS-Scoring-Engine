from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router
from dotenv import load_dotenv
import os
import base64
import tempfile
load_dotenv()
app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix="/api/v1")

def setup_google_credentials():
    """
    Sets up Google Cloud credentials for the application.
    It first checks for a Base64 encoded credential string (for production environments).
    If not found, it falls back to checking for a file path (for local development from .env).
    """
    # Priority 1: Use Base64 encoded credentials if available (e.g., in production)
    encoded_creds = os.environ.get('GCP_CREDS_BASE64')
    if encoded_creds:
        try:
            decoded_creds_bytes = base64.b64decode(encoded_creds)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as temp_file:
                temp_file.write(decoded_creds_bytes.decode('utf-8'))
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file.name
            print("✅ Google Cloud credentials loaded from Base64 environment variable.")
            return
        except Exception as e:
            print(f"❌ Failed to load credentials from Base64 string: {e}")

setup_google_credentials()

@app.get("/")
def root():
    return {"message": "ATS Scoring Engine is Running"}