from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

# ─── MEVCUT (v3) ─────────────────────────────────────────────────────────────

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    skills = Column(JSON, default=[])
    experience = Column(JSON, default=[])
    education = Column(JSON, default=[])
    certifications = Column(JSON, default=[])
    projects = Column(JSON, default=[])
    seniority_level = Column(String, nullable=True)
    seniority_score = Column(Float, nullable=True)
    strengths = Column(JSON, default=[])
    areas_for_improvement = Column(JSON, default=[])
    original_filename = Column(String, nullable=True)
    upload_status = Column(String, default="Pending")
    # v4 new fields
    rating = Column(Float, nullable=True)          # 1-5 yıldız
    notes = Column(Text, nullable=True)             # İK notları
    tags = Column(JSON, default=[])                 # Etiketler
    is_favorite = Column(Boolean, default=False)
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")

class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    department = Column(String, nullable=True)
    description = Column(Text)
    required_skills = Column(JSON, default=[])
    preferred_skills = Column(JSON, default=[])
    min_experience_years = Column(Integer, default=0)
    seniority_level = Column(String, nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String, default="TRY")
    # v4 new fields
    is_active = Column(Boolean, default=True)
    location = Column(String, nullable=True)
    headcount = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    applications = relationship("Application", back_populates="position", cascade="all, delete-orphan")

# ─── YENİ (v4) ───────────────────────────────────────────────────────────────

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    # Pipeline status: applied|screening|interview|offer|hired|rejected
    status = Column(String, default="applied")
    status_history = Column(JSON, default=[])   # [{status, date, note}]
    # AI match scores (copied from matcher at application time)
    match_score = Column(Float, nullable=True)
    semantic_score = Column(Float, nullable=True)
    keyword_score = Column(Float, nullable=True)
    matching_skills = Column(JSON, default=[])
    # HR fields
    cover_letter = Column(Text, nullable=True)
    hr_notes = Column(Text, nullable=True)
    source = Column(String, nullable=True)       # linkedin, kariyer.net, direkt...
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    hired_at = Column(DateTime(timezone=True), nullable=True)
    # Relations
    candidate = relationship("Candidate", back_populates="applications")
    position = relationship("Position", back_populates="applications")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
    offer = relationship("Offer", back_populates="application", uselist=False, cascade="all, delete-orphan")

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    round_number = Column(Integer, default=1)
    interview_type = Column(String, default="hr")   # hr|technical|video|onsite
    status = Column(String, default="scheduled")    # scheduled|completed|cancelled
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, default=60)
    location = Column(String, nullable=True)
    meeting_link = Column(String, nullable=True)
    interviewer_name = Column(String, nullable=True)
    # Scores
    overall_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    cultural_score = Column(Float, nullable=True)
    # Notes & AI
    notes = Column(Text, nullable=True)
    strengths_noted = Column(JSON, default=[])
    concerns_noted = Column(JSON, default=[])
    recommendation = Column(String, nullable=True)  # proceed|reject|hold
    ai_questions = Column(JSON, default=[])          # AI üretimi mülakat soruları
    ai_summary = Column(Text, nullable=True)         # AI mülakat özeti
    result = Column(String, nullable=True)           # "passed", "failed", "pending"
    result_note = Column(Text, nullable=True)        # Sonuç notu
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    application = relationship("Application", back_populates="interviews")

class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    status = Column(String, default="draft")    # draft|sent|accepted|rejected|negotiating
    proposed_salary = Column(Integer, nullable=True)
    final_salary = Column(Integer, nullable=True)
    currency = Column(String, default="TRY")
    start_date = Column(DateTime(timezone=True), nullable=True)
    position_title = Column(String, nullable=True)
    benefits = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    negotiation_history = Column(JSON, default=[])
    letter_content = Column(Text, nullable=True)   # AI üretimi teklif mektubu
    sent_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    application = relationship("Application", back_populates="offer")

class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)       # Evrak|IT|Eğitim|Tanışma
    responsible = Column(String, nullable=True)    # İK|IT|Yönetici|Aday
    due_days = Column(Integer, default=1)
    status = Column(String, default="pending")     # pending|in_progress|completed|skipped
    completed_at = Column(DateTime(timezone=True), nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

import enum
class UserRole(enum.Enum):
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    CANDIDATE = "candidate" # Portal erişimi için

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(JSON, default=UserRole.HR.value) # default role
    # SQLAlchemy enum handling can be tricky, using JSON/String for simplicity in this project
    # But auth.py expects .role to be an Enum-like or at least comparable.
    # Let's use Column(String) and wrap with property or just use String.
    role = Column(String, default=UserRole.HR.value)
    department = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # candidate specific
    candidate_access_token = Column(String, nullable=True, index=True)

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True) # İleride auth eklendiğinde
    user_name = Column(String, default="Admin")
    action = Column(String)  # 'candidate_added', 'status_changed', etc.
    target_type = Column(String) # 'candidate', 'application', etc.
    target_id = Column(Integer)
    details = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
