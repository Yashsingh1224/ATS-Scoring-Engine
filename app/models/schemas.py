from pydantic import BaseModel

from typing import List, Optional



# --- Internal Models for Analysis ---

class EntityExperience(BaseModel):

    role: Optional[str] = None

    years: float = 0.0



class ResumeEntities(BaseModel):

    name: Optional[str] = None

    email: Optional[str] = None

    skills: List[str] = []

    experience: List[EntityExperience] = []

    total_experience_years: float = 0.0

    projects: List[str] = []

    education: List[str] = []

    sections: List[str] = []



class JDEntities(BaseModel):

    required_skills: List[str] = []

    min_experience_years: float = 0.0

    preferred_skills: List[str] = []

    role_responsibilities: List[str] = []



# --- Response Models for API ---

class ScoreBreakdown(BaseModel):

    skill_score: float

    experience_score: float

    project_score: float

    section_score: float



class MatchResponse(BaseModel):

    total_score: float

    breakdown: ScoreBreakdown

    missing_skills: List[str]

    matched_skills: List[str]

    summary: str