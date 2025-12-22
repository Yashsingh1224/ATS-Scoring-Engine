import google.generativeai as genai

import json

import pypdf

import io

import logging

from app.core.config import settings

from app.models.schemas import ResumeEntities

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GOOGLE_API_KEY)



class ResumeProcessor:

    def extract_text_from_pdf(self, file_content: bytes) -> str:

        """Read PDF bytes and return raw string."""

        try:

            reader = pypdf.PdfReader(io.BytesIO(file_content))

            text = ""

            for page in reader.pages:

                text += page.extract_text() + "\n"

            return text

        except Exception as e:

            logger.error(f"PDF extraction error: {type(e).__name__}: {e}")

            raise



    def extract_entities(self, raw_text: str) -> ResumeEntities:

        """Send raw text to Gemini and get structured JSON."""

        if not raw_text or len(raw_text.strip()) == 0:

            logger.error("Empty resume text provided")

            raise ValueError("Resume text cannot be empty")

            

        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={"temperature": 0.0}
        )

        

        prompt = f"""

        You are an ATS parser. Extract data from this resume into JSON.

        Strict JSON Schema:

        {{

            "name": "string",

            "email": "string",

            "skills": ["skill1", "skill2"],

            "total_experience_years": float (sum of all roles),

            "projects": ["title1", "title2"],

            "education": ["degree1"]

        }}

        Resume Text:

        {raw_text[:10000]}

        """

        try:

            logger.info("Calling Gemini API for resume extraction...")

            response = model.generate_content(prompt)

            logger.debug(f"Gemini response received: {response.text[:100]}...")

            

            clean_json = response.text.replace('```json', '').replace('```', '').strip()

            data = json.loads(clean_json)

            logger.info(f"Successfully extracted resume entities: {len(data.get('skills', []))} skills found")

            return ResumeEntities(**data)

        except json.JSONDecodeError as e:

            logger.error(f"JSON parsing error in resume extraction: {e}")

            raise ValueError(f"Failed to parse Gemini response as JSON: {e}")

        except Exception as e:

            logger.error(f"Gemini Resume Error: {type(e).__name__}: {e}")

            raise