"""
Candidate Portal Router — Aday Kendi Başvurusunu Takip Eder
Token ile güvenli erişim — e-posta ile gönderilen link aracılığıyla.

GET  /api/portal/me                — Aday profili
GET  /api/portal/applications      — Aday başvuruları
GET  /api/portal/applications/{id} — Başvuru detayı (mülakat, teklif)
POST /api/portal/offer/{id}/accept — Teklifi kabul et
POST /api/portal/offer/{id}/reject — Teklifi reddet
GET  /api/portal/notifications     — Bildirimler
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List

from .. import models, schemas
from ..database import get_db
from ..auth import get_candidate_from_token, get_current_user

router = APIRouter()


def _get_portal_user(
    token: str = Query(..., description="Portal erişim tokenı"),
    db: Session = Depends(get_db),
) -> models.User:
    return get_candidate_from_token(token, db)


@router.get("/me")
def get_portal_profile(
    db: Session = Depends(get_db),
    portal_user: models.User = Depends(_get_portal_user),
):
    """Aday kendi profil bilgisini görür."""
    candidate = db.query(models.Candidate).filter(
        models.Candidate.user_id == portal_user.id
    ).first()

    return {
        "user": {
            "id": portal_user.id,
            "full_name": portal_user.full_name,
            "email": portal_user.email,
        },
        "candidate": {
            "id": candidate.id if candidate else None,
            "name": candidate.name if candidate else portal_user.full_name,
            "skills": candidate.skills if candidate else [],
            "seniority_level": candidate.seniority_level if candidate else None,
        } if candidate else None,
    }


@router.get("/applications")
def get_portal_applications(
    db: Session = Depends(get_db),
    portal_user: models.User = Depends(_get_portal_user),
):
    """Aday tüm başvurularını görür."""
    candidate = db.query(models.Candidate).filter(
        models.Candidate.user_id == portal_user.id
    ).first()

    if not candidate:
        return []

    applications = db.query(models.Application).options(
        joinedload(models.Application.position),
        joinedload(models.Application.interviews),
        joinedload(models.Application.offer),
    ).filter(
        models.Application.candidate_id == candidate.id
    ).order_by(models.Application.applied_at.desc()).all()

    result = []
    for app in applications:
        # Adaya gösterilen bilgileri filtrele (iç notları gizle)
        interviews_data = []
        for iv in app.interviews:
            interviews_data.append({
                "id": iv.id,
                "interview_type": iv.interview_type.value,
                "status": iv.status.value,
                "round_number": iv.round_number,
                "scheduled_at": iv.scheduled_at.isoformat() if iv.scheduled_at else None,
                "duration_minutes": iv.duration_minutes,
                "meeting_link": iv.meeting_link if iv.status.value == "scheduled" else None,
                "location": iv.location if iv.status.value == "scheduled" else None,
            })

        offer_data = None
        if app.offer and app.offer.status != models.OfferStatus.DRAFT:
            offer_data = {
                "id": app.offer.id,
                "status": app.offer.status.value,
                "proposed_salary": app.offer.proposed_salary,
                "currency": app.offer.currency,
                "start_date": app.offer.start_date.isoformat() if app.offer.start_date else None,
                "benefits": app.offer.benefits,
                "letter_content": app.offer.letter_content,
                "expires_at": app.offer.expires_at.isoformat() if app.offer.expires_at else None,
            }

        result.append({
            "id": app.id,
            "status": app.status.value,
            "applied_at": app.applied_at.isoformat(),
            "position": {
                "id": app.position.id if app.position else None,
                "title": app.position.title if app.position else None,
                "department": app.position.department if app.position else None,
                "location": app.position.location if app.position else None,
            } if app.position else None,
            "status_history": [
                {
                    "status": h.get("status"),
                    "changed_at": h.get("changed_at"),
                    "note": h.get("note"),
                }
                for h in (app.status_history or [])
                if h.get("status") not in ["screening"]  # Bazı iç durumları gizle
            ],
            "interviews": interviews_data,
            "offer": offer_data,
        })

    return result


@router.post("/offer/{offer_id}/accept")
def accept_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    portal_user: models.User = Depends(_get_portal_user),
):
    """Aday teklifi kabul eder."""
    offer = db.query(models.Offer).options(
        joinedload(models.Offer.application).joinedload(models.Application.candidate)
    ).filter(models.Offer.id == offer_id).first()

    if not offer:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı")

    # Teklif bu adaya mı ait?
    candidate = db.query(models.Candidate).filter(
        models.Candidate.user_id == portal_user.id
    ).first()
    if not candidate or offer.application.candidate_id != candidate.id:
        raise HTTPException(status_code=403, detail="Bu teklife erişim yetkiniz yok")

    if offer.status not in [models.OfferStatus.SENT, models.OfferStatus.NEGOTIATING]:
        raise HTTPException(status_code=400, detail="Bu teklif kabul edilebilir durumda değil")

    from datetime import timezone
    from datetime import datetime
    offer.status = models.OfferStatus.ACCEPTED
    offer.responded_at = datetime.now(timezone.utc)
    offer.final_salary = offer.proposed_salary

    if offer.application:
        offer.application.status = models.ApplicationStatus.HIRED
        offer.application.hired_at = datetime.now(timezone.utc)
        history = offer.application.status_history or []
        history.append({
            "status": "hired",
            "changed_at": datetime.now(timezone.utc).isoformat(),
            "changed_by": candidate.name,
            "note": "Aday teklifi kabul etti",
        })
        offer.application.status_history = history

    db.commit()
    return {"message": "Teklif kabul edildi. Sizi ekibimizde görmekten heyecan duyuyoruz!"}


@router.post("/offer/{offer_id}/reject")
def reject_offer(
    offer_id: int,
    reason: str = Query(default=""),
    db: Session = Depends(get_db),
    portal_user: models.User = Depends(_get_portal_user),
):
    """Aday teklifi reddeder."""
    offer = db.query(models.Offer).options(
        joinedload(models.Offer.application).joinedload(models.Application.candidate)
    ).filter(models.Offer.id == offer_id).first()

    if not offer:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı")

    candidate = db.query(models.Candidate).filter(
        models.Candidate.user_id == portal_user.id
    ).first()
    if not candidate or offer.application.candidate_id != candidate.id:
        raise HTTPException(status_code=403, detail="Bu teklife erişim yetkiniz yok")

    from datetime import timezone, datetime
    offer.status = models.OfferStatus.REJECTED
    offer.responded_at = datetime.now(timezone.utc)
    if reason:
        offer.notes = f"{offer.notes or ''}\nRed gerekçesi: {reason}"

    if offer.application:
        offer.application.status = models.ApplicationStatus.OFFER_REJECTED

    db.commit()
    return {"message": "Teklif reddedildi"}


@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    portal_user: models.User = Depends(_get_portal_user),
):
    """Aday bildirimlerini görür."""
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == portal_user.id
    ).order_by(models.Notification.created_at.desc()).limit(20).all()

    # Okunmamışları okundu yap
    for n in notifications:
        if not n.is_read:
            n.is_read = True
    db.commit()

    return [schemas.NotificationOut.model_validate(n) for n in notifications]
