from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime, timezone
import json, os
import models, database

router = APIRouter()

DEFAULT_TASKS = [
    {"title": "Kimlik belgelerini teslim et", "category": "Evrak", "responsible": "Aday", "due_days": 1},
    {"title": "İş sözleşmesini imzala", "category": "Evrak", "responsible": "İK", "due_days": 1},
    {"title": "SGK bildirimi", "category": "Evrak", "responsible": "İK", "due_days": 1},
    {"title": "Kurumsal e-posta oluştur", "category": "IT Setup", "responsible": "IT", "due_days": 1},
    {"title": "Bilgisayar/ekipman teslimi", "category": "IT Setup", "responsible": "IT", "due_days": 1},
    {"title": "Sistem erişim yetkileri", "category": "IT Setup", "responsible": "IT", "due_days": 2},
    {"title": "Ekip tanıtımı", "category": "Tanışma", "responsible": "Yönetici", "due_days": 1},
    {"title": "Oryantasyon eğitimi", "category": "Eğitim", "responsible": "İK", "due_days": 3},
    {"title": "İş güvenliği eğitimi", "category": "Eğitim", "responsible": "İK", "due_days": 3},
    {"title": "Banka hesap bilgilerini ver", "category": "Evrak", "responsible": "Aday", "due_days": 2},
    {"title": "30 günlük hedef belirleme", "category": "Performans", "responsible": "Yönetici", "due_days": 5},
    {"title": "1. ay değerlendirme görüşmesi", "category": "Performans", "responsible": "Yönetici", "due_days": 30},
]

@router.post("/{app_id}/generate")
def generate_checklist(app_id: int, db: Session = Depends(database.get_db)):
    app = db.query(models.Application).options(
        joinedload(models.Application.position),
        joinedload(models.Application.candidate),
    ).filter(models.Application.id == app_id).first()
    if not app: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    # Clear existing
    db.query(models.OnboardingTask).filter(models.OnboardingTask.application_id == app_id).delete()
    extra = []
    key = os.getenv("GEMINI_API_KEY")
    if key and app.position:
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})
            prompt = f"""
{app.position.title} pozisyonu için 3-4 ek onboarding görevi öner.
Departman: {app.position.department or 'Genel'}
JSON: {{"tasks": [{{"title": "...", "category": "...", "responsible": "İK/IT/Yönetici/Aday", "due_days": 1}}]}}
"""
            resp = model.generate_content(prompt)
            result = json.loads(resp.text)
            extra = result.get("tasks", [])
        except: pass
    all_tasks = DEFAULT_TASKS + extra
    created = []
    for i, t in enumerate(all_tasks):
        task = models.OnboardingTask(
            application_id=app_id, title=t["title"], category=t.get("category"),
            responsible=t.get("responsible"), due_days=t.get("due_days", 1),
            order_index=i, status="pending",
        )
        db.add(task)
        created.append(task)
    # Update app status to hired
    app.status = "hired"
    app.hired_at = datetime.now(timezone.utc)
    db.commit()
    return {"count": len(created), "tasks": [{"id": t.id, "title": t.title, "category": t.category, "responsible": t.responsible, "due_days": t.due_days, "status": t.status} for t in created]}

@router.get("/{app_id}")
def get_tasks(app_id: int, db: Session = Depends(database.get_db)):
    tasks = db.query(models.OnboardingTask).filter(
        models.OnboardingTask.application_id == app_id
    ).order_by(models.OnboardingTask.due_days, models.OnboardingTask.order_index).all()
    return [{"id": t.id, "title": t.title, "category": t.category, "responsible": t.responsible, "due_days": t.due_days, "status": t.status, "completed_at": t.completed_at.isoformat() if t.completed_at else None} for t in tasks]

@router.patch("/task/{task_id}")
def update_task(task_id: int, status: str, db: Session = Depends(database.get_db)):
    task = db.query(models.OnboardingTask).filter(models.OnboardingTask.id == task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Görev bulunamadı")
    task.status = status
    if status == "completed": task.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": task.status}
