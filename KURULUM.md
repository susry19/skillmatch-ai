# SkillMatch AI v4 — Kurulum Rehberi

## Gereksinimler

- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ (opsiyonel, yalnızca frontend geliştirme için)

---

## 1. PostgreSQL Kurulumu

### Windows
1. [postgresql.org](https://www.postgresql.org/download/windows/) adresinden indirin
2. Kurulum sırasında şifre belirleyin
3. pgAdmin veya psql ile bağlanın:

```sql
CREATE DATABASE skillmatch;
CREATE USER skillmatch WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE skillmatch TO skillmatch;
```

### macOS (Homebrew)
```bash
brew install postgresql@16
brew services start postgresql@16
psql postgres -c "CREATE DATABASE skillmatch;"
psql postgres -c "CREATE USER skillmatch WITH PASSWORD 'password';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE skillmatch TO skillmatch;"
```

### Linux (Ubuntu/Debian)
```bash
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE DATABASE skillmatch;"
sudo -u postgres psql -c "CREATE USER skillmatch WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE skillmatch TO skillmatch;"
```

---

## 2. Proje Kurulumu

```bash
# Projeyi klonla
git clone <repo-url> skillmatch-v4
cd skillmatch-v4/backend

# Sanal ortam oluştur
python -m venv venv
source venv/bin/activate    # Linux/macOS
.\venv\Scripts\activate     # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt
```

---

## 3. Ortam Değişkenleri

```bash
cp .env.example .env
```

`.env` dosyasını düzenle:

```env
DATABASE_URL=postgresql://skillmatch:password@localhost:5432/skillmatch
SECRET_KEY=python -c "import secrets; print(secrets.token_hex(32))"
GEMINI_API_KEY=your-gemini-api-key
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-email-password
```

---

## 4. Veritabanı Migration

```bash
# Alembic başlat (ilk kurulumda)
alembic init alembic

# alembic.ini dosyasında sqlalchemy.url güncelle:
# sqlalchemy.url = postgresql://skillmatch:password@localhost:5432/skillmatch

# Migration oluştur ve çalıştır
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

**VEYA** — migration olmadan direkt tablo oluşturma (geliştirme için):
```python
# Python'da bir kez çalıştır:
from backend.database import engine, Base
from backend import models
Base.metadata.create_all(bind=engine)
```

---

## 5. İlk Kullanıcı Oluşturma

Uygulama başlatıldıktan sonra ilk kayıt olan kullanıcı otomatik olarak ADMIN rolü alır:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@skillmatch.ai","password":"Admin1234!","full_name":"Sistem Yöneticisi","role":"admin"}'
```

---

## 6. Uygulamayı Başlat

```bash
# Geliştirme modu (hot-reload)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Veya run.bat (Windows)
```

Uygulama: **http://localhost:8000**
API Docs: **http://localhost:8000/api/docs**

---

## 7. Eski SQLite Veritabanından Veri Aktarma

Eğer SkillMatch AI v3'ten (SQLite) geçiyorsanız:

```python
# migrate_sqlite_to_pg.py
import sqlite3
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend import models
from backend.database import Base

# SQLite bağlantısı
sqlite_conn = sqlite3.connect("skillmatch.db")
sqlite_conn.row_factory = sqlite3.Row

# PostgreSQL engine
pg_engine = create_engine("postgresql://skillmatch:password@localhost:5432/skillmatch")
Base.metadata.create_all(bind=pg_engine)

with Session(pg_engine) as session:
    # Adayları aktar
    for row in sqlite_conn.execute("SELECT * FROM candidates").fetchall():
        candidate = models.Candidate(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            summary=row["summary"],
            skills=json.loads(row["skills"] or "[]"),
            experience=json.loads(row["experience"] or "[]"),
            education=json.loads(row["education"] or "[]"),
            certifications=json.loads(row["certifications"] or "[]"),
            seniority_level=row["seniority_level"],
            seniority_score=row["seniority_score"],
            original_filename=row["original_filename"],
            upload_status=row["upload_status"],
        )
        session.merge(candidate)

    # Pozisyonları aktar
    for row in sqlite_conn.execute("SELECT * FROM positions").fetchall():
        position = models.Position(
            id=row["id"],
            title=row["title"],
            department=row["department"],
            description=row["description"],
            required_skills=json.loads(row["required_skills"] or "[]"),
            preferred_skills=json.loads(row["preferred_skills"] or "[]"),
        )
        session.merge(position)

    session.commit()
    print("Migration tamamlandı!")
```

---

## 8. Kullanıcı Rolleri

| Rol | Erişim |
|-----|--------|
| `admin` | Tam erişim + kullanıcı yönetimi |
| `hr` | Aday, pozisyon, başvuru, mülakat, teklif |
| `manager` | Kendi departmanının başvuruları ve mülakatları |
| `candidate` | Sadece kendi başvurusu (portal üzerinden) |

---

## 9. Aday Portal Kullanımı

1. İK uzmanı adaya portal token'ı oluşturur:
   ```
   POST /api/auth/users/{user_id}/generate-candidate-token
   ```
2. Sistem otomatik olarak adaya portal linki içeren e-posta gönderir
3. Aday `https://domain.com/portal?token=xxx` bağlantısıyla portala erişir
4. Portal üzerinden: başvuru durumu, mülakat bilgileri, teklif görüntüleme ve kabul/ret

---

## 10. E-posta Yapılandırması

### SendGrid (Önerilen)
```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=SG.xxxxxxxxxx
MAIL_STARTTLS=True
```

### Gmail
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-app-password    # 2FA açıkken App Password kullan
MAIL_STARTTLS=True
```
