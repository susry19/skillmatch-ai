from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timezone
import json
from .. import models, schemas, database
from ..services.matcher import matcher_service

router = APIRouter()

def _push_history(app, status, note=None):
    h = app.status_history or []
    h.append({"status": status, "date": datetime.now(timezone.utc).isoformat(), "note": note})
    app.status_history = h
    app.status = status

@router.post("/", response_model=schemas.ApplicationOut, status_code=201)
def create_application(data: schemas.ApplicationCreate, db: Session = Depends(database.get_db)):
    exists = db.query(models.Application).filter(
        models.Application.candidate_id == data.candidate_id,
        models.Application.position_id == data.position_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Bu aday bu pozisyon için zaten başvurmuş")
    candidate = db.query(models.Candidate).filter(models.Candidate.id == data.candidate_id).first()
    position = db.query(models.Position).filter(models.Position.id == data.position_id).first()
    if not candidate or not position:
        raise HTTPException(status_code=404, detail="Aday veya pozisyon bulunamadı")
    # Compute AI match score
    matches = matcher_service.match_candidates(data.position_id, db)
    score_data = next((m for m in matches if m["candidate"].id == data.candidate_id), None)
    app = models.Application(
        candidate_id=data.candidate_id, position_id=data.position_id,
        status="applied",
        status_history=[{"status": "applied", "date": datetime.now(timezone.utc).isoformat(), "note": "Başvuru oluşturuldu"}],
        cover_letter=data.cover_letter, source=data.source,
        match_score=score_data["score"] if score_data else None,
        semantic_score=score_data.get("semantic_score") if score_data else None,
        keyword_score=score_data.get("keyword_score") if score_data else None,
        matching_skills=score_data.get("matching_skills", []) if score_data else [],
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return _load(app.id, db)

@router.get("/", response_model=List[schemas.ApplicationOut])
def list_applications(position_id: Optional[int]=None, status: Optional[str]=None, db: Session = Depends(database.get_db)):
    q = db.query(models.Application).options(joinedload(models.Application.candidate), joinedload(models.Application.position))
    if position_id: q = q.filter(models.Application.position_id == position_id)
    if status: q = q.filter(models.Application.status == status)
    return q.order_by(models.Application.applied_at.desc()).all()

@router.get("/pipeline")
def get_pipeline(position_id: Optional[int]=None, db: Session = Depends(database.get_db)):
    q = db.query(models.Application).options(joinedload(models.Application.candidate), joinedload(models.Application.position))
    if position_id: q = q.filter(models.Application.position_id == position_id)
    apps = q.order_by(models.Application.match_score.desc().nullslast()).all()
    stages = ["applied","screening","interview","offer","hired","rejected"]
    labels = {"applied":"Başvurdu","screening":"Değerlendirme","interview":"Mülakat","offer":"Teklif","hired":"İşe Alındı","rejected":"Elendi"}
    cols = []
    for s in stages:
        group = [_app_dict(a) for a in apps if a.status == s]
        cols.append({"status": s, "label": labels[s], "count": len(group), "applications": group})
    return {"columns": cols, "total": len(apps)}

def _load(app_id, db):
    return db.query(models.Application).options(
        joinedload(models.Application.candidate), joinedload(models.Application.position)
    ).filter(models.Application.id == app_id).first()

def _app_dict(a):
    c = a.candidate
    p = a.position
    return {
        "id": a.id, "status": a.status, "match_score": a.match_score,
        "semantic_score": a.semantic_score, "keyword_score": a.keyword_score,
        "matching_skills": a.matching_skills or [], "hr_notes": a.hr_notes,
        "applied_at": a.applied_at.isoformat() if a.applied_at else None,
        "source": a.source,
        "candidate": {"id": c.id, "name": c.name, "email": c.email, "seniority_level": c.seniority_level,
                      "skills": c.skills or [], "rating": c.rating, "is_favorite": c.is_favorite,
                      "summary": c.summary, "original_filename": c.original_filename} if c else None,
        "position": {"id": p.id, "title": p.title, "department": p.department} if p else None,
    }

@router.get("/{app_id}", response_model=schemas.ApplicationOut)
def get_application(app_id: int, db: Session = Depends(database.get_db)):
    a = _load(app_id, db)
    if not a: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    return a

@router.patch("/{app_id}/status")
def update_status(app_id: int, data: schemas.ApplicationStatusUpdate, db: Session = Depends(database.get_db)):
    a = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not a: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    old_status = a.status
    _push_history(a, data.status, data.note)
    if data.status == "hired": a.hired_at = datetime.now(timezone.utc)
    db.commit()
    
    # Log the transition
    from candidates import _log
    _log(db, "status_changed", "application", a.id, {"from": old_status, "to": a.status, "candidate_id": a.candidate_id})
    
    return {"status": a.status}

@router.put("/{app_id}/notes")
def update_hr_notes(app_id: int, notes: str, db: Session = Depends(database.get_db)):
    a = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not a: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    a.hr_notes = notes
    db.commit()
    return {"ok": True}

@router.delete("/{app_id}", status_code=204)
def delete_application(app_id: int, db: Session = Depends(database.get_db)):
    a = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not a: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    db.delete(a)
    db.commit()
