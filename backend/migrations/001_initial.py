"""
Alembic migration — İlk kurulum.
Tüm tabloları oluşturur: users, candidates, positions, applications,
interviews, offers, onboarding_tasks, notifications

Çalıştırma:
  alembic upgrade head
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users tablosu
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), default="hr", nullable=False),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("candidate_access_token", sa.String(), unique=True, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()")),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
    )

    # candidates tablosu
    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(), index=True),
        sa.Column("email", sa.String(), index=True, nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("skills", sa.JSON(), default=[]),
        sa.Column("experience", sa.JSON(), default=[]),
        sa.Column("education", sa.JSON(), default=[]),
        sa.Column("certifications", sa.JSON(), default=[]),
        sa.Column("projects", sa.JSON(), default=[]),
        sa.Column("seniority_level", sa.String(), nullable=True),
        sa.Column("seniority_score", sa.Float(), nullable=True),
        sa.Column("strengths", sa.JSON(), default=[]),
        sa.Column("areas_for_improvement", sa.JSON(), default=[]),
        sa.Column("original_filename", sa.String(), nullable=True),
        sa.Column("upload_status", sa.String(), default="Pending"),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()")),
    )

    # positions tablosu
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("title", sa.String(), index=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("description", sa.Text()),
        sa.Column("required_skills", sa.JSON(), default=[]),
        sa.Column("preferred_skills", sa.JSON(), default=[]),
        sa.Column("min_experience_years", sa.Integer(), default=0),
        sa.Column("seniority_level", sa.String(), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(), default="TRY"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("headcount", sa.Integer(), default=1),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("remote_allowed", sa.Boolean(), default=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()")),
    )

    # applications tablosu
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("position_id", sa.Integer(), sa.ForeignKey("positions.id"), nullable=False),
        sa.Column("status", sa.String(), default="applied", nullable=False),
        sa.Column("status_history", sa.JSON(), default=[]),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("semantic_score", sa.Float(), nullable=True),
        sa.Column("keyword_score", sa.Float(), nullable=True),
        sa.Column("matching_skills", sa.JSON(), default=[]),
        sa.Column("hr_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.String(), nullable=True),
        sa.Column("cover_letter", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()")),
        sa.Column("hired_at", sa.DateTime(timezone=True), nullable=True),
    )

    # interviews tablosu
    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("interviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("interview_type", sa.String(), default="hr"),
        sa.Column("status", sa.String(), default="scheduled"),
        sa.Column("round_number", sa.Integer(), default=1),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), default=60),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("meeting_link", sa.String(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("technical_score", sa.Float(), nullable=True),
        sa.Column("cultural_fit_score", sa.Float(), nullable=True),
        sa.Column("communication_score", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("strengths_noted", sa.JSON(), default=[]),
        sa.Column("concerns_noted", sa.JSON(), default=[]),
        sa.Column("recommendation", sa.String(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()")),
    )

    # offers tablosu
    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id"), nullable=False, unique=True),
        sa.Column("status", sa.String(), default="draft"),
        sa.Column("proposed_salary", sa.Integer(), nullable=True),
        sa.Column("final_salary", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(), default="TRY"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("position_title", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("benefits", sa.JSON(), default=[]),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("negotiation_history", sa.JSON(), default=[]),
        sa.Column("letter_content", sa.Text(), nullable=True),
        sa.Column("letter_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()")),
    )

    # onboarding_tasks tablosu
    op.create_table(
        "onboarding_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("responsible", sa.String(), nullable=True),
        sa.Column("due_days_after_start", sa.Integer(), default=1),
        sa.Column("status", sa.String(), default="pending"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()")),
    )

    # notifications tablosu
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("link", sa.String(), nullable=True),
        sa.Column("is_read", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("onboarding_tasks")
    op.drop_table("offers")
    op.drop_table("interviews")
    op.drop_table("applications")
    op.drop_table("positions")
    op.drop_table("candidates")
    op.drop_table("users")
