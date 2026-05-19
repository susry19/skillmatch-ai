from sqlalchemy.orm import Session
from .. import models
import json
from semantic_matcher import semantic_matcher

class MatcherService:
    def match_candidates(self, position_id: int, db: Session):
        position = db.query(models.Position).filter(models.Position.id == position_id).first()
        if not position:
            return []

        candidates = db.query(models.Candidate).all()
        matches = []

        required_skills = set(s.lower() for s in position.required_skills) if position.required_skills else set()
        
        # Prepare Position Text for Semantics
        pos_text = f"{position.title} {position.description} {' '.join(position.required_skills or [])}"

        for candidate in candidates:
            # --- 1. KEYWORD SCORE (40 points max) ---
            keyword_score = 0
            candidate_skills = set(s.lower() for s in candidate.skills) if candidate.skills else set()
            
            if required_skills:
                overlap = candidate_skills.intersection(required_skills)
                skill_ratio = len(overlap) / len(required_skills)
                keyword_score = skill_ratio * 40.0
            else:
                keyword_score = 20.0 # If no skills required, give partial default score

            # --- 2. EXPERIENCE / SENIORITY SCORE (20 points max) ---
            experience_score = 0
            if candidate.seniority_level and position.seniority_level:
                c_sen = candidate.seniority_level.lower()
                p_sen = position.seniority_level.lower()
                
                if c_sen == p_sen:
                    experience_score = 20.0
                elif p_sen in ["junior", "entry"] and c_sen in ["mid", "senior"]:
                    experience_score = 15.0 # Overqualified is okay
                elif p_sen == "mid" and c_sen == "senior":
                    experience_score = 15.0
                else:
                    experience_score = 5.0 # Wrong seniority
            else:
                experience_score = 10.0 # Default fallback if missing info
            
            # --- 3. SEMANTIC SCORE (40 points max) ---
            semantic_score = 0
            learning_boost = 0
            confidence = "High"

            try:
                # Construct Candidate Text
                exp_text = " ".join([f"{e.get('title','')} {e.get('description','')}" for e in (candidate.experience or [])])
                cand_text = f"{candidate.name} {candidate.summary} {' '.join(candidate.skills or [])} {exp_text}"
                
                # Get Scores
                semantic_score_100 = semantic_matcher.calculate_semantic_score(cand_text, pos_text)
                learning_boost = semantic_matcher.get_learning_boost(candidate.skills, candidate.seniority_level)
                
                if semantic_score_100 > 0:
                    semantic_score = (semantic_score_100 / 100.0) * 40.0
                else:
                    # Fallback logic if semantic fails or is exactly 0
                    semantic_score = (keyword_score / 40.0) * 40.0 # Mirror keyword score
                    confidence = "Low (Semantic Failed)"

            except Exception as e:
                print(f"[Matcher] ML failed for {candidate.name}: {e}")
                semantic_score = (keyword_score / 40.0) * 40.0
                confidence = "Low (ML Error)"

            # --- 4. FINAL CALCULATION ---
            # Total Base Score = 40 + 40 + 20 = 100
            final_score = keyword_score + experience_score + semantic_score + learning_boost
            
            # Adjust to avoid extremely low scores unless truly irrelevant
            if final_score < 20 and len(candidate_skills) > 0:
                final_score += 15.0 # Minimum baseline for having any skills
                
            final_score = min(final_score, 100.0)

            matches.append({
                "candidate": candidate,
                "score": round(final_score, 1),
                "matching_skills": list(candidate_skills.intersection(required_skills)),
                # Additional fields
                "semantic_score": round(semantic_score_100 if 'semantic_score_100' in locals() else 0, 1),
                "learning_boost": round(learning_boost, 1),
                "keyword_score": round(keyword_score * 2.5, 1), # Normalize back to 0-100 for UI if needed
                "confidence": confidence
            })

        # Sort by score desc
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches

matcher_service = MatcherService()
