from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class CandidateBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    experience: List[Any] = []
    education: List[Any] = []
    certifications: List[str] = []
    seniority_level: Optional[str] = None
    seniority_score: Optional[float] = None
    strengths: List[str] = []
    areas_for_improvement: List[str] = []

class CandidateCreate(CandidateBase):
    original_filename: str

class Candidate(CandidateBase):
    id: int
    upload_status: str
    rating: Optional[float] = None
    notes: Optional[str] = None
    tags: List[str] = []
    is_favorite: bool = False
    is_blacklisted: bool = False
    blacklist_reason: Optional[str] = None
    created_at: datetime
    applications: List[Any] = []
    class Config:
        from_attributes = True

class PositionBase(BaseModel):
    title: str
    department: Optional[str] = None
    description: str
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    min_experience_years: Optional[int] = 0
    seniority_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = "TRY"
    is_active: Optional[bool] = True
    location: Optional[str] = None
    headcount: Optional[int] = 1

class PositionCreate(PositionBase):
    pass

class Position(PositionBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class ApplicationCreate(BaseModel):
    candidate_id: int
    position_id: int
    cover_letter: Optional[str] = None
    source: Optional[str] = None

class ApplicationStatusUpdate(BaseModel):
    status: str
    note: Optional[str] = None

class ApplicationOut(BaseModel):
    id: int
    candidate_id: int
    position_id: int
    status: str
    status_history: List[Any] = []
    match_score: Optional[float] = None
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    matching_skills: List[str] = []
    hr_notes: Optional[str] = None
    cover_letter: Optional[str] = None
    source: Optional[str] = None
    applied_at: datetime
    hired_at: Optional[datetime] = None
    candidate: Optional[Candidate] = None
    position: Optional[Position] = None
    class Config:
        from_attributes = True

class InterviewCreate(BaseModel):
    application_id: int
    interview_type: str = "hr"
    round_number: int = 1
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = 60
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    interviewer_name: Optional[str] = None

class InterviewFeedback(BaseModel):
    overall_score: Optional[float] = None
    technical_score: Optional[float] = None
    cultural_score: Optional[float] = None
    notes: Optional[str] = None
    strengths_noted: List[str] = []
    concerns_noted: List[str] = []
    recommendation: Optional[str] = None
    result: Optional[str] = "pending"
    result_note: Optional[str] = None

class InterviewOut(BaseModel):
    id: int
    application_id: int
    round_number: int
    interview_type: str
    status: str
    scheduled_at: Optional[datetime] = None
    duration_minutes: int
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    interviewer_name: Optional[str] = None
    overall_score: Optional[float] = None
    technical_score: Optional[float] = None
    cultural_score: Optional[float] = None
    notes: Optional[str] = None
    strengths_noted: List[str] = []
    concerns_noted: List[str] = []
    recommendation: Optional[str] = None
    ai_questions: List[Any] = []
    ai_summary: Optional[str] = None
    result: Optional[str] = None
    result_note: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class OfferCreate(BaseModel):
    application_id: int
    proposed_salary: Optional[int] = None
    currency: str = "TRY"
    start_date: Optional[datetime] = None
    position_title: Optional[str] = None
    benefits: List[str] = []
    notes: Optional[str] = None

class OfferOut(BaseModel):
    id: int
    application_id: int
    status: str
    proposed_salary: Optional[int] = None
    final_salary: Optional[int] = None
    currency: str
    start_date: Optional[datetime] = None
    position_title: Optional[str] = None
    benefits: List[str] = []
    notes: Optional[str] = None
    negotiation_history: List[Any] = []
    letter_content: Optional[str] = None
    sent_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class OnboardingTaskOut(BaseModel):
    id: int
    application_id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    responsible: Optional[str] = None
    due_days: int
    status: str
    completed_at: Optional[datetime] = None
    order_index: int
    created_at: datetime
    class Config:
        from_attributes = True

class MatchResult(BaseModel):
    candidate_id: int
    candidate_name: str
    match_score: float
    match_reasons: List[str]
    missing_skills: List[str]

class CandidateMatch(BaseModel):
    candidate: Candidate
    score: float
    matching_skills: List[str]
    semantic_score: Optional[float] = 0.0
    keyword_score: Optional[float] = 0.0
    learning_boost: Optional[float] = 0.0

class CandidateComparisonRequest(BaseModel):
    candidate_ids: List[int]
    position_id: Optional[int] = None

class ComparisonRow(BaseModel):
    criteria: str
    candidate1_val: str
    candidate2_val: str

class CandidateComparisonResponse(BaseModel):
    comparison: str
    recommendation: str
    candidate1_pros: List[str]
    candidate2_pros: List[str]
    comparison_table: List[ComparisonRow]

class FeedbackCreate(BaseModel):
    candidate_id: int
    position_id: int
    signal_type: str

class CandidateRatingUpdate(BaseModel):
    rating: float

class CandidateNotesUpdate(BaseModel):
    notes: str

class LogOut(BaseModel):
    id: int
    user_name: str
    action: str
    target_type: str
    target_id: int
    details: Any
    created_at: datetime
    class Config:
        from_attributes = True

class InterviewResultUpdate(BaseModel):
    result: str
    result_note: Optional[str] = None

# AUTH SCHEMAS
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Any # Using Any to avoid circular dependency problems for now

class UserBase(BaseModel):
    email: str
    full_name: str
    department: Optional[str] = None
    role: str = "hr"
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str

class UserRoleUpdate(BaseModel):
    role: str
