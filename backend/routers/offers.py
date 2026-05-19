from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone, timedelta
import json, os
import models, schemas, database

router = APIRouter()

@router.post("/", response_model=schemas.OfferOut, status_code=201)
def create_offer(data: schemas.OfferCreate, db: Session = Depends(database.get_db)):
    app = db.query(models.Application).options(
        joinedload(models.Application.position)
    ).filter(models.Application.id == data.application_id).first()
    if not app: raise HTTPException(status_code=404, detail="Başvuru bulunamadı")
    existing = db.query(models.Offer).filter(models.Offer.application_id == data.application_id).first()
    if existing: raise HTTPException(status_code=400, detail="Bu başvuru için zaten teklif mevcut")
    offer = models.Offer(
        application_id=data.application_id, status="draft",
        proposed_salary=data.proposed_salary, currency=data.currency,
        start_date=data.start_date,
        position_title=data.position_title or (app.position.title if app.position else None),
        benefits=data.benefits, notes=data.notes, negotiation_history=[],
    )
    db.add(offer)
    app.status = "offer"
    h = app.status_history or []
    h.append({"status": "offer", "date": datetime.now(timezone.utc).isoformat(), "note": "Teklif oluşturuldu"})
    app.status_history = h
    db.commit()
    db.refresh(offer)
    return offer

@router.get("/application/{app_id}", response_model=schemas.OfferOut)
def get_offer(app_id: int, db: Session = Depends(database.get_db)):
    offer = db.query(models.Offer).filter(models.Offer.application_id == app_id).first()
    if not offer: raise HTTPException(status_code=404, detail="Teklif bulunamadı")
    return offer

@router.patch("/{offer_id}/status")
def update_offer_status(offer_id: int, status: str, db: Session = Depends(database.get_db)):
    offer = db.query(models.Offer).options(
        joinedload(models.Offer.application)
    ).filter(models.Offer.id == offer_id).first()
    if not offer: raise HTTPException(status_code=404, detail="Teklif bulunamadı")
    offer.status = status
    offer.responded_at = datetime.now(timezone.utc)
    if status == "accepted":
        offer.final_salary = offer.proposed_salary
        if offer.application:
            offer.application.status = "hired"
            offer.application.hired_at = datetime.now(timezone.utc)
    elif status == "sent":
        offer.sent_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": offer.status}

@router.post("/{offer_id}/generate-letter")
def generate_letter(offer_id: int, db: Session = Depends(database.get_db)):
    """AI ile kişiselleştirilmiş teklif mektubu üret."""
    offer = db.query(models.Offer).options(
        joinedload(models.Offer.application).joinedload(models.Application.candidate),
        joinedload(models.Offer.application).joinedload(models.Application.position),
    ).filter(models.Offer.id == offer_id).first()
    if not offer: raise HTTPException(status_code=404, detail="Teklif bulunamadı")
    candidate = offer.application.candidate if offer.application else None
    position = offer.application.position if offer.application else None
    benefits_str = "\n".join([f"- {b}" for b in (offer.benefits or [])])
    start_str = offer.start_date.strftime("%d %B %Y") if offer.start_date else "Müzakere edilecek"
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        offer.letter_content = f"""Sayın {candidate.name if candidate else 'Aday'},\n\n{offer.position_title or 'Pozisyon'} pozisyonu için işe alım teklifimizi sunmaktan memnuniyet duyarız.\n\nAylık net maaş: {offer.proposed_salary:,} {offer.currency}\nBaşlangıç Tarihi: {start_str}\n\nSaygılarımızla,\nİK Departmanı"""
        db.commit()
        return {"letter": offer.letter_content}
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})
        prompt = f"""
Profesyonel, sıcak ve kurumsal bir iş teklifi mektubu yaz (Türkçe).

Aday: {candidate.name if candidate else 'Aday'}
Pozisyon: {offer.position_title or (position.title if position else 'Pozisyon')}
Maaş: {offer.proposed_salary:,} {offer.currency} / aylık net
Başlangıç: {start_str}
Yan Haklar: {benefits_str or "Belirtilmemiş"}
Notlar: {offer.notes or ""}

Mektupta: selamlama, pozisyon ve koşullar, maaş+yan haklar, başlangıç tarihi, kabul süresi (7 gün), profesyonel kapanış olsun.

JSON: {{"letter": "mektup metni"}}
"""
        resp = model.generate_content(prompt)
        result = json.loads(resp.text)
        offer.letter_content = result.get("letter", "")
    except Exception as e:
        offer.letter_content = f"Sayın {candidate.name if candidate else 'Aday'},\n\n{offer.position_title or 'Pozisyon'} için teklifimizi sunuyoruz.\n\nMaaş: {offer.proposed_salary:,} {offer.currency}/ay\nBaşlangıç: {start_str}\n\nSaygılarımızla,\nİK Departmanı"
    db.commit()
    return {"letter": offer.letter_content}
