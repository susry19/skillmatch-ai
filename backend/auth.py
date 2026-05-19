"""
JWT tabanlı kimlik doğrulama servisi.
- Şifre hash/verify (bcrypt)
- JWT token üretimi ve doğrulaması
- Kullanıcı bağımlılık enjeksiyonu
- Rol tabanlı erişim kontrolü
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from config import settings
import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ─── Şifre İşlemleri ─────────────────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ─── JWT Token ───────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token geçersiz veya süresi dolmuş",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── Kullanıcı Bağımlılıkları ─────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    payload = decode_token(token)
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token içinde kullanıcı ID bulunamadı")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Hesap devre dışı")
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    return current_user


# ─── Rol Tabanlı Erişim Kontrolü (RBAC) ───────────────────────────────────────

def require_roles(*roles: models.UserRole):
    """
    Kullanıcının belirtilen rollerden birine sahip olmasını zorunlu kılar.
    Kullanım: Depends(require_roles(UserRole.HR, UserRole.ADMIN))
    """
    def checker(current_user: models.User = Depends(get_current_user)):
        allowed = [r.value if hasattr(r, 'value') else r for r in roles]
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bu işlem için yetkiniz yok. Gerekli rol: {allowed}"
            )
        return current_user
    return checker


def require_hr_or_admin(current_user: models.User = Depends(get_current_user)):
    """İK veya Admin rolü gerektirir."""
    if current_user.role not in [models.UserRole.HR.value, models.UserRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Bu işlem için İK veya Admin yetkisi gerekli")
    return current_user


def require_manager_or_above(current_user: models.User = Depends(get_current_user)):
    """Yönetici, İK veya Admin rolü gerektirir."""
    if current_user.role not in [models.UserRole.MANAGER.value, models.UserRole.HR.value, models.UserRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Bu işlem için Yönetici veya üzeri yetki gerekli")
    return current_user


# ─── Aday Token Girişi (Portal) ───────────────────────────────────────────────

def get_candidate_from_token(
    token: str,
    db: Session = Depends(get_db)
) -> models.User:
    """
    Adayın portal erişimi için kullandığı statik token ile kullanıcı döndürür.
    URL parametresi olarak ?token=xxx şeklinde kullanılır.
    """
    user = db.query(models.User).filter(
        models.User.candidate_access_token == token,
        models.User.is_active == True
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Geçersiz erişim tokenı")
    return user
