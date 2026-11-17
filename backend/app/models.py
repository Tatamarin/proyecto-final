"""Modelo relacional de SDLC-AI."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


test_case_criteria = Table(
    "test_case_criteria",
    Base.metadata,
    Column("test_case_id", ForeignKey("test_cases.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "acceptance_criteria_id",
        ForeignKey("acceptance_criteria.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


def utc_now() -> datetime:
    """Return naive UTC for compatibility with the current database schema."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    needs = relationship("Need", back_populates="project", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="project", cascade="all, delete-orphan")

class Need(Base):
    __tablename__ = "needs"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(30), default="USER", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    project = relationship("Project", back_populates="needs")
    requirements = relationship("Requirement", back_populates="need", cascade="all, delete-orphan")

class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    agent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    executions = relationship("AIExecution", back_populates="prompt_version")
    __table_args__ = (UniqueConstraint("agent_type", "version", name="uq_prompt_agent_version"),)

class AIExecution(Base):
    __tablename__ = "ai_executions"
    id: Mapped[int] = mapped_column(primary_key=True)
    prompt_version_id: Mapped[int | None] = mapped_column(ForeignKey("prompt_versions.id", ondelete="SET NULL"))
    agent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(100))
    input_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_json: Mapped[dict | None] = mapped_column(JSON)
    temperature: Mapped[float | None] = mapped_column()
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    prompt_version = relationship("PromptVersion", back_populates="executions")
    requirements = relationship("Requirement", back_populates="ai_execution")
    test_cases = relationship("TestCase", back_populates="ai_execution")

class Requirement(Base):
    __tablename__ = "requirements"
    id: Mapped[int] = mapped_column(primary_key=True)
    need_id: Mapped[int] = mapped_column(ForeignKey("needs.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_execution_id: Mapped[int | None] = mapped_column(ForeignKey("ai_executions.id", ondelete="SET NULL"))
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(30), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="GENERATED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    need = relationship("Need", back_populates="requirements")
    ai_execution = relationship("AIExecution", back_populates="requirements")
    acceptance_criteria = relationship("AcceptanceCriteria", back_populates="requirement", cascade="all, delete-orphan")
    tests = relationship("TestCase", back_populates="requirement", cascade="all, delete-orphan")
    reviews = relationship("HumanReview", back_populates="requirement", foreign_keys="HumanReview.requirement_id", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("need_id", "code", name="uq_requirement_need_code"),)

class AcceptanceCriteria(Base):
    __tablename__ = "acceptance_criteria"
    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirement = relationship("Requirement", back_populates="acceptance_criteria")
    tests = relationship(
        "TestCase",
        secondary=test_case_criteria,
        back_populates="acceptance_criteria",
    )
    __table_args__ = (UniqueConstraint("requirement_id", "code", name="uq_acceptance_requirement_code"),)

class TestCase(Base):
    __tablename__ = "test_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_execution_id: Mapped[int | None] = mapped_column(ForeignKey("ai_executions.id", ondelete="SET NULL"))
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    preconditions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    test_data: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="GENERATED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    requirement = relationship("Requirement", back_populates="tests")
    ai_execution = relationship("AIExecution", back_populates="test_cases")
    acceptance_criteria = relationship(
        "AcceptanceCriteria",
        secondary=test_case_criteria,
        back_populates="tests",
    )
    steps = relationship("TestCaseStep", back_populates="test_case", cascade="all, delete-orphan", order_by="TestCaseStep.step_order")
    reviews = relationship("HumanReview", back_populates="test_case", foreign_keys="HumanReview.test_case_id", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("requirement_id", "code", name="uq_test_requirement_code"),)

class TestCaseStep(Base):
    __tablename__ = "test_case_steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    test_case = relationship("TestCase", back_populates="steps")
    __table_args__ = (UniqueConstraint("test_case_id", "step_order", name="uq_test_step_order"),)

class HumanReview(Base):
    __tablename__ = "human_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int | None] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"))
    test_case_id: Mapped[int | None] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"))
    reviewer: Mapped[str] = mapped_column(String(150), nullable=False, default="system")
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    original_value: Mapped[dict | None] = mapped_column(JSON)
    new_value: Mapped[dict | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    requirement = relationship("Requirement", back_populates="reviews", foreign_keys=[requirement_id])
    test_case = relationship("TestCase", back_populates="reviews", foreign_keys=[test_case_id])
    __table_args__ = (CheckConstraint("(requirement_id IS NOT NULL) <> (test_case_id IS NOT NULL)", name="ck_review_single_target"),)

class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(nullable=False)
    metric_type: Mapped[str] = mapped_column(String(30), default="GAUGE", nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    project = relationship("Project", back_populates="metrics")
    __table_args__ = (Index("ix_metrics_project_name", "project_id", "metric_name"),)
