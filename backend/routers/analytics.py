from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, schemas, database
from typing import List
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/stats")
def get_stats(db: Session = Depends(database.get_db)):
    total_candidates = db.query(models.Candidate).count()
    total_positions = db.query(models.Position).count()
    
    # --- AI Insights ---
    # Find most common skill (Mocking logic for demo if DB is small, else aggregation)
    all_skills = []
    candidates = db.query(models.Candidate).all()
    for c in candidates:
        if c.skills:
            all_skills.extend(c.skills if isinstance(c.skills, list) else [])
    
    trending_skill = "Python"
    if all_skills:
        trending_skill = max(set(all_skills), key=all_skills.count)

    # Top Position
    top_position = db.query(models.Position).first()
    top_pos_title = top_position.title if top_position else "Genel Başvuru"
    
    # Best Match (Mock)
    highlight_candidate = "Bulunamadı"
    highlight_score = 0
    if candidates:
        highlight_candidate = candidates[0].name
        highlight_score = int(candidates[0].seniority_score) if candidates[0].seniority_score else 85

    ai_insights = {
        "trending_skill": trending_skill,
        "top_position": top_pos_title,
        "highlight_candidate": highlight_candidate,
        "highlight_score": highlight_score,
        "position_iq": "Yazılım pozisyonları için aday havuzu güçlü, ancak Satış rolleri için ilan güncellenmeli."
    }

    # --- Charts Data (Mocked/Calculated) ---
    # Candidate Growth (Last 7 days)
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%d Pa") for i in range(6, -1, -1)]
    # Mocking growth data for visual effect
    growth_data = [random.randint(2, 15) for _ in range(7)] 
    
    # Skill Cloud (Top 5)
    skill_counts = {}
    for s in all_skills:
        skill_counts[s] = skill_counts.get(s, 0) + 1
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    skill_cloud = {"labels": [s[0] for s in sorted_skills], "data": [s[1] for s in sorted_skills]}
    
    # Seniority Distribution (Real)
    seniority_dist = {
        "Junior": db.query(models.Candidate).filter(models.Candidate.seniority_level == "Junior").count(),
        "Mid": db.query(models.Candidate).filter(models.Candidate.seniority_level == "Mid").count(),
        "Senior": db.query(models.Candidate).filter(models.Candidate.seniority_level == "Senior").count(),
    }

    # Performance Metrics
    performance = {
        "avg_process_time": "3.2s",
        "process_trend_sub": "- %7", # decreasing
        "match_accuracy": "93%",
        "accuracy_trend_up": "+ %3"
    }

    return {
        "total_candidates": total_candidates,
        "total_positions": total_positions,
        "sub_stats": {
             "candidates_trend": "+12%",
             "positions_trend": "+2"
        },
        "ai_insights": ai_insights,
        "charts": {
            "growth": {"labels": dates, "data": growth_data},
            "skills": skill_cloud,
            "seniority": seniority_dist
        },
        "performance": performance
    }

@router.get("/logs", response_model=List[schemas.LogOut])
def get_logs(limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.Log).order_by(models.Log.created_at.desc()).limit(limit).all()
