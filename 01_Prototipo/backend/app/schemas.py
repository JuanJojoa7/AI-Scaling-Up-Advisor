from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Question(BaseModel):
    id: str
    module: str
    text: str
    type: str  # text|number|multi
    options: Optional[List[str]] = None
    weight: float = 1.0


class AnswerIn(BaseModel):
    session_id: int
    question_id: str
    module: str
    value: Any


class ScoreResult(BaseModel):
    people: float
    strategy: float
    execution: float
    cash: float


class ReportOut(BaseModel):
    session_id: int
    scores: ScoreResult
    narrative: str
    priorities: List[str]
    recommendations: List[str]
    resources: List[str]
    pdf_url: Optional[str] = None
