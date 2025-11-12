from datetime import datetime
from typing import Optional, List, Dict
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    sessions: List["DiagSession"] = Relationship(back_populates="user")


class DiagSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    status: str = Field(default="in_progress")  # in_progress|completed
    current_module: str = Field(default="onboarding")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="sessions")
    answers: List["Answer"] = Relationship(back_populates="session")
    report: Optional["Report"] = Relationship(back_populates="session")


class Answer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="diagsession.id")
    module: str  # people|strategy|execution|cash
    question_id: str
    raw_value: str  # store as text (will be encrypted on write)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: Optional[DiagSession] = Relationship(back_populates="answers")


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="diagsession.id")
    scores_json: str  # {people, strategy, execution, cash}
    narrative: str
    priorities_json: str  # [..]
    recommendations_json: str  # [..]
    resources_json: str  # [..]
    radar_image_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: Optional[DiagSession] = Relationship(back_populates="report")
