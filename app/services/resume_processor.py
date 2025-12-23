import json
import pypdf
import io
import logging
from app.services.model_manager import ModelManager
from app.models.schemas import ResumeEntities

logger = logging.getLogger(__name__)

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



    def extract_entities(self, raw_text: str, job_description_title: str = None) -> ResumeEntities:

        """Send raw text to Vertex AI and get structured JSON."""

        if not raw_text or len(raw_text.strip()) == 0:

            logger.error("Empty resume text provided")

            raise ValueError("Resume text cannot be empty")
            
        experience_instruction = "total_experience_years: float (sum of all roles)"
        if job_description_title:
             experience_instruction = f"total_experience_years: float (sum of years ONLY for roles relevant to the target job '{job_description_title}'. Ignore unrelated experience like HR if applying for Engineering)"

        model_manager = ModelManager()
        

        prompt = f"""

        You are an ATS parser. Extract data from this resume into JSON.
        Identify the distinct section headers present in the resume (e.g., "Summary", "Work Experience", "Education", "Skills", "Projects", "Certifications", "Contact") and list them in the "sections" field.
        Also, perform a brief check for spelling and grammatical errors in the resume text. List any significant errors found in the "grammar_errors" field. If none are found, return an empty list.

        Strict JSON Schema:

        {{

            "name": "string",

            "email": "string",

            "skills": ["skill1", "skill2"],

            "{experience_instruction}",

            "projects": ["title1", "title2"],

            "education": ["degree1"],

            "sections": ["Section Header 1", "Section Header 2"],
            
            "grammar_errors": ["Spelling error: 'manger' instead of 'manager'", "Grammar error: 'I has worked'"]

        }}

        Resume Text:

        {raw_text[:10000]}

        """

        try:

            logger.info("Calling Vertex AI for resume extraction...")

            data = model_manager.generate_content(prompt)

            logger.info(f"Successfully extracted resume entities: {len(data.get('skills', []))} skills found")

            return ResumeEntities(**data)

        except Exception as e:

            logger.error(f"Vertex AI Resume Error: {type(e).__name__}: {e}")

            raise