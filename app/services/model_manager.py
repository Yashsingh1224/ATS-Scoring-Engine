import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import logging
import json
import re
import time
import random
from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelManager:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            if not settings.GCP_PROJECT_ID:
                logger.warning("GCP_PROJECT_ID not set. Vertex AI might fail if not running in an environment with default project.")
            
            vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION)
            # Using a default model, can be overridden
            self._model = GenerativeModel("gemini-2.5-flash-lite") 
            logger.info(f"Vertex AI initialized with project {settings.GCP_PROJECT_ID} in {settings.GCP_LOCATION}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise

    def generate_content(self, prompt: str, max_retries: int = 3) -> dict:
        """
        Generates content using Vertex AI and returns parsed JSON.
        """
        generation_config = GenerationConfig(
            temperature=0.0,
            response_mime_type="application/json"
        )

        last_error = None
        for attempt in range(max_retries):
            try:
                response = self._model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                content = response.text
                # Basic cleanup if model returns markdown blocks despite mime_type
                clean_json = content.replace('```json', '').replace('```', '').strip()
                
                try:
                    return json.loads(clean_json)
                except json.JSONDecodeError:
                    # Fallback regex extraction
                    match = re.search(r"\{[\s\S]*\}", content, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
                    else:
                        raise ValueError("No JSON object found in response")

            except Exception as e:
                last_error = e
                logger.warning(f"Vertex AI attempt {attempt + 1} failed: {e}")
                time.sleep((2 ** attempt) + random.uniform(0, 1))
        
        logger.error(f"Vertex AI failed after {max_retries} attempts")
        raise last_error
