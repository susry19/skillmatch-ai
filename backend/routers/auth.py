"""
Auth Router — Kullanıcı kaydı, girişi ve profil yönetimi.
POST /api/auth/register  — Yeni kullanıcı oluştur
POST /api/auth/login     — JWT token al
GET  /api/auth/me        — Mevcut kullanıcı bilgisi
PUT  /api/auth/me        — Profil güncelleme
POST /api/auth/change-password
GET  /api/auth/users     — Tüm kullanıcılar (Admin/HR)
"""
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, require_roles
)

router = APIRouter()


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """Yeni kullanıcı kaydı. İlk kullanıcı otomatik ADMIN olur."""
    # E-posta kontrolü
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı")

    # İlk kullanıcıyı admin yap
    user_count = db.query(models.User).count()
    # Ensure role is a string value
    role_val = models.UserRole.ADMIN.value if user_count == 0 else user_data.role

    user = models.User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=role_val,
        department=user_data.department,
        phone=user_data.phone,
        is_active=True,
        is_verified=True,  # Şimdilik e-posta doğrulaması olmadan aktif
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(
    credentials: schemas.LoginRequest,
    db: Session = Depends(get_db),
):
    """JWT token ile giriş yap."""
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Hesap devre dışı bırakılmış")

    # Son giriş zamanını güncelle
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    user_out = schemas.UserOut.model_validate(user)
    return schemas.Token(access_token=token, user=user_out.model_dump())


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Oturum açmış kullanıcının bilgilerini döndürür."""
    return current_user


@router.put("/me", response_model=schemas.UserOut)
def update_me(
    update_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Profil güncelleme."""
    for field, value in update_data.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password")
def change_password(
    data: schemas.UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Şifre değişikliği."""
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifre hatalı")
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Şifre başarıyla güncellendi"}


@router.get("/users", response_model=List[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles(models.UserRole.ADMIN, models.UserRole.HR)
    ),
):
    """Tüm kullanıcıları listele (Admin ve HR)."""
    return db.query(models.User).filter(models.User.is_active == True).all()


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN)),
):
    """Kullanıcı hesabını devre dışı bırak (Admin only)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Kendi hesabınızı devre dışı bırakamazsınız")
    user.is_active = False
    db.commit()
    return {"message": f"{user.full_name} hesabı devre dışı bırakıldı"}


@router.post("/users/{user_id}/generate-candidate-token")
def generate_candidate_token(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles(models.UserRole.ADMIN, models.UserRole.HR)
    ),
):
    """Aday için portal erişim tokenı üretir."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

    token = secrets.token_urlsafe(32)
    user.candidate_access_token = token
    db.commit()

    from ..config import settings
    portal_url = f"{settings.APP_URL}/portal?token={token}"
    return {"token": token, "portal_url": portal_url}


@router.patch("/users/{user_id}/role", response_model=schemas.UserOut)
def update_user_role(
    user_id: int,
    data: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN)),
):
    """Kullanıcı rolünü güncelle (Admin only)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    user.role = data.role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN)),
):
    """Kullanıcıyı tamamen sil (Admin only)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Kendi hesabınızı silemezsiniz")
    
    db.delete(user)
    db.commit()
    return None
