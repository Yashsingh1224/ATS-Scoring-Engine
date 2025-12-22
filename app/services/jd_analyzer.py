import google.generativeai as genai

import json

import logging

from app.core.config import settings

from app.models.schemas import JDEntities



logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GOOGLE_API_KEY)



class JDAnalyzer:

    def analyze(self, jd_text: str) -> JDEntities:

        if not jd_text or len(jd_text.strip()) == 0:

            logger.error("Empty job description text provided")

            raise ValueError("Job description text cannot be empty")

            

        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={"temperature": 0.0}
        )

        

        prompt = f"""

        Extract job requirements into JSON.

        Strict JSON Schema:

        {{

            "required_skills": ["skill1", "skill2"],

            "min_experience_years": float,

            "preferred_skills": ["skill3"],

            "role_responsibilities": ["resp1"]

        }}

    
        Job Description:

        {jd_text}

        """

        try:

            logger.info("Calling Gemini API for job description analysis...")

            response = model.generate_content(prompt)

            logger.debug(f"Gemini response received: {response.text[:100]}...")

            clean_json = response.text.replace('```json', '').replace('```', '').strip()

            data = json.loads(clean_json)

            logger.info(f"Successfully extracted JD entities: {len(data.get('required_skills', []))} required skills found")

            return JDEntities(**data)

        except json.JSONDecodeError as e:

            logger.error(f"JSON parsing error in JD analysis: {e}")

            raise ValueError(f"Failed to parse Gemini response as JSON: {e}")

        except Exception as e:

            logger.error(f"Gemini JD Error: {type(e).__name__}: {e}")

            raise

