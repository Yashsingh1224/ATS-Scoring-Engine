from app.models.schemas import ResumeEntities, JDEntities, MatchResponse, ScoreBreakdown
import difflib

class ScoringEngine:
    
    COMMON_SYNONYMS = {
        "react": "reactjs",
        "react.js": "reactjs",
        "aws": "amazon web services",
        "js": "javascript",
        "ts": "typescript",
        "node": "nodejs",
        "node.js": "nodejs",
        "py": "python",
        "golang": "go",
        "c++": "cpp",
        "dot net": ".net",
        "dotnet": ".net"
    }

    REQUIRED_SECTIONS = [
        "summary",
        "experience", 
        "education", 
        "skills", 
        "projects"
    ]

    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill string: lowercase, strip, resolve synonyms."""
        s = skill.lower().strip()
        return self.COMMON_SYNONYMS.get(s, s)

    def _normalize_section(self, section: str) -> str:
        """Normalize section name for comparison."""
        s = section.lower().strip()
        # Common variations mapping
        if "work" in s or "employment" in s or "history" in s:
            return "experience"
        if "academic" in s or "qualification" in s:
            return "education"
        if "tech" in s or "competencies" in s:
            return "skills"
        if "pro" in s and "file" in s: # Profile
            return "summary"
        if "objective" in s:
            return "summary"
        return s

    def _is_match(self, skill1: str, skill2: str, threshold: float = 0.85) -> bool:
        """Check if two skills match using fuzzy string comparison."""
        norm1 = self._normalize_skill(skill1)
        norm2 = self._normalize_skill(skill2)
        
        # Exact match after normalization
        if norm1 == norm2:
            return True
        
        # Substring match (e.g., "react" in "react js")
        if len(norm1) > 3 and len(norm2) > 3:
             if norm1 in norm2 or norm2 in norm1:
                 return True

        # Fuzzy match using SequenceMatcher
        similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= threshold

    def calculate_score(self, resume: ResumeEntities, jd: JDEntities, weights: dict = None) -> MatchResponse:
        # 1. Skills Scoring (Weight 50%)
        # Normalize weights if provided
        skill_weights = {self._normalize_skill(k): v for k, v in weights.items()} if weights else {}
        
        # Normalize JD and Resume skills
        # We keep original names for display but use normalized for matching
        jd_skills_map = {self._normalize_skill(s): s for s in jd.required_skills}
        res_skills_list = [self._normalize_skill(s) for s in resume.skills]
        
        matched_display = []
        missing_display = []
        
        total_possible_weight = 0.0
        earned_weight = 0.0
        
        if not jd_skills_map:
            # No required skills? Treat as full match for skills component.
            skill_score = 50.0
        else:
            for norm_jd_skill, raw_jd_skill in jd_skills_map.items():
                weight = skill_weights.get(norm_jd_skill, 1.0)
                total_possible_weight += weight
                
                # Check for match in resume skills
                found = False
                for norm_res_skill in res_skills_list:
                    if self._is_match(norm_jd_skill, norm_res_skill):
                        found = True
                        break
                
                if found:
                    earned_weight += weight
                    matched_display.append(raw_jd_skill)
                else:
                    missing_display.append(raw_jd_skill)
            
            if total_possible_weight > 0:
                skill_score = (earned_weight / total_possible_weight) * 50.0
            else:
                skill_score = 0.0

        # 2. Experience Scoring (Weight 25%)
        # More robust experience logic with buffer
        EXP_BUFFER = 0.5  # Allow 0.5 years deficit to still get nearly full points
        MAX_EXP_SCORE = 25.0
        
        if jd.min_experience_years == 0:
            exp_score = MAX_EXP_SCORE
        elif resume.total_experience_years >= jd.min_experience_years:
            exp_score = MAX_EXP_SCORE
        else:
            diff = jd.min_experience_years - resume.total_experience_years
            if diff <= EXP_BUFFER:
                # Penalty is reduced if within buffer (approx 93% of max score)
                exp_score = MAX_EXP_SCORE * 0.93
            else:
                # Linear drop-off
                ratio = resume.total_experience_years / jd.min_experience_years
                exp_score = min(ratio * MAX_EXP_SCORE, MAX_EXP_SCORE)

        # 3. Project Scoring (Weight 10%)
        # Adjusted weight from 20 to 10 for project scoring
        project_count = len(resume.projects)
        if project_count >= 2:
            project_score = 10.0
        elif project_count == 1:
            project_score = 5.0
        else:
            project_score = 0.0

        # 4. Section Scoring (Weight 10%)
        # Check for presence of required sections
        found_sections = [self._normalize_section(s) for s in resume.sections]
        matched_sections = 0
        for required in self.REQUIRED_SECTIONS:
            # Simple substring check after normalization
            if any(required in s for s in found_sections):
                matched_sections += 1
            # Fallback checks if specific lists are populated even if header wasn't explicit
            elif required == "skills" and resume.skills:
                matched_sections += 1
            elif required == "experience" and resume.experience:
                matched_sections += 1
            elif required == "projects" and resume.projects:
                matched_sections += 1
            elif required == "education" and resume.education:
                matched_sections += 1

        # Calculate section score (2 points per section for 5 sections = 10 points)
        section_score = (matched_sections / len(self.REQUIRED_SECTIONS)) * 10.0

        # 5. Grammar & Spelling Scoring (Weight 5%)
        # Deduct 1 point per error found
        error_count = len(resume.grammar_errors)
        grammar_score = max(5.0 - error_count, 0.0)

        # 6. Final Score Calculation
        total_score = round(skill_score + exp_score + project_score + section_score + grammar_score, 2)

        # 7. Create Response Object
        breakdown = ScoreBreakdown(
            skill_score=round(skill_score, 2),
            experience_score=round(exp_score, 2),
            project_score=round(project_score, 2),
            section_score=round(section_score, 2),
            spelling_and_grammar_score=round(grammar_score, 2)
        )

        summary = (
            f"Candidate Score: {total_score}/100. "
            f"Skills: {int(skill_score)}/50. "
            f"Exp: {int(exp_score)}/25. "
            f"Proj: {int(project_score)}/10. "
            f"Sections: {int(section_score)}/10. "
            f"Grammar: {int(grammar_score)}/5 ({error_count} errors)."
        )

        return MatchResponse(
            total_score=total_score,
            breakdown=breakdown,
            missing_skills=missing_display,
            matched_skills=matched_display,
            summary=summary
        )