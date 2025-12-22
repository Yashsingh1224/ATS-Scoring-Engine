from app.models.schemas import ResumeEntities, JDEntities, MatchResponse, ScoreBreakdown

class ScoringEngine:
    def calculate_score(self, resume: ResumeEntities, jd: JDEntities, weights: dict = None) -> MatchResponse:
        # 1. Skills Scoring (Weight 50%)
        res_skills = set(s.lower() for s in resume.skills)
        jd_skills = set(s.lower() for s in jd.required_skills)
        
        # Normalize weights to lowercase if provided
        skill_weights = {k.lower(): v for k, v in weights.items()} if weights else {}

        if not jd_skills:
            skill_score = 50.0
            matched = []
            missing = []
        else:
            matched = list(res_skills.intersection(jd_skills))
            missing = list(jd_skills - res_skills)
            
            # Calculate weighted score
            total_possible_weight = 0.0
            earned_weight = 0.0
            
            for skill in jd_skills:
                weight = skill_weights.get(skill, 1.0)
                total_possible_weight += weight
                if skill in res_skills:
                    earned_weight += weight
            
            if total_possible_weight > 0:
                skill_score = (earned_weight / total_possible_weight) * 50.0
            else:
                skill_score = 0.0

        # 2. Experience Scoring (Weight 30%)
        if jd.min_experience_years == 0:
            exp_score = 30.0
        elif resume.total_experience_years >= jd.min_experience_years:
            exp_score = 30.0
        else:
            # Gradual score for experience mismatch
            ratio = resume.total_experience_years / jd.min_experience_years
            exp_score = min(ratio * 30.0, 30.0)

        # 3. Project Scoring (Weight 20%)
        # Simple check if resume has any projects listed
        if resume.projects:
            project_score = 20.0
        else:
            project_score = 0.0

        # 4. Final Score Calculation
        total_score = round(skill_score + exp_score + project_score, 2)

        # 5. Create Response Object
        breakdown = ScoreBreakdown(
            skill_score=round(skill_score, 2),
            experience_score=round(exp_score, 2),
            project_score=round(project_score, 2)
        )

        summary = (
            f"The candidate's resume shows a good fit for the role. "
            f"They possess {len(matched)} of the {len(jd_skills)} required skills. "
            f"With {resume.total_experience_years} years of experience, they "
            f"{'meet' if resume.total_experience_years >= jd.min_experience_years else 'do not meet'} the minimum requirement of {jd.min_experience_years} years. "
            f"The resume {'includes' if resume.projects else 'does not include'} project work."
        )

        return MatchResponse(
            total_score=total_score,
            breakdown=breakdown,
            missing_skills=missing,
            matched_skills=matched,
            summary=summary
        )


