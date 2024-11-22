from http.client import HTTPException
import os
from google.oauth2 import service_account
from google.cloud import translate_v2 as translate
from typing import Optional
import html

from dotenv import load_dotenv
load_dotenv()

GOOGLE_SERVICE_KEY = {
    "type": "service_account",
    "project_id": os.getenv("GOOGLE_SHEET_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_SHEET_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_SHEET_PRIVATE_KEY"),
    "client_email": os.getenv("GOOGLE_SHEET_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_SHEET_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("GOOGLE_SHEET_CERT_URL"),
    "universe_domain": "googleapis.com"
}

# Initialize the Google Cloud Translate client
accessor = service_account.Credentials.from_service_account_info(GOOGLE_SERVICE_KEY)
translate_client = translate.Client(credentials=accessor)

async def translate_text(text: str, target_language: str, source_language: Optional[str] = None):
    try:
        # Call the Google Cloud Translate API
        if source_language: # Source lang specified
            result = translate_client.translate(
                text, 
                target_language=target_language, 
                source_language=source_language
            )
        else: # No source lang specified
            result = translate_client.translate(
                text, 
                target_language=target_language
            )
        final = html.unescape(result['translatedText']) # Fix special characters
        return final
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))