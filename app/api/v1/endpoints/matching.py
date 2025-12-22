from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.resume_processor import ResumeProcessor
from app.services.jd_analyzer import JDAnalyzer
from app.services.scoring_engine import ScoringEngine
from app.models.schemas import MatchResponse

router = APIRouter()

# Instantiate services once
resume_processor = ResumeProcessor()
jd_analyzer = JDAnalyzer()
scorer = ScoringEngine()

@router.post("/score", response_model=MatchResponse)
async def score_resume(
    resume_file: UploadFile = File(...),
    jd_text: str = Form(...)
):
    # 1. Read PDF
    if resume_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    file_content = await resume_file.read()
    raw_resume_text = resume_processor.extract_text_from_pdf(file_content)
    
    if not raw_resume_text:
        raise HTTPException(status_code=400, detail="Could not read PDF text")

    # 2. Extract Entities (Gemini)
    resume_data = resume_processor.extract_entities(raw_resume_text)
    jd_data = jd_analyzer.analyze(jd_text)
    
    # 3. Calculate Score (Math)
    result = scorer.calculate_score(resume_data, jd_data)
    
    return result