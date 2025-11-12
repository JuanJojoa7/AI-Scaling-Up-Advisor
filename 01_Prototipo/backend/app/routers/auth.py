from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from passlib.hash import pbkdf2_sha256
from jose import jwt
from datetime import datetime, timedelta
import os

from ..database import get_session, init_db
from ..models import User
from ..schemas import UserCreate, UserLogin, Token

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8


@router.on_event("startup")
def startup():
    init_db()


def create_access_token(sub: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": sub, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)


def get_password_hash(password: str) -> str:
    # Truncar si excede 200 chars para evitar uso indebido
    if len(password) > 200:
        password = password[:200]
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    if len(password) > 200:
        password = password[:200]
    return pbkdf2_sha256.verify(password, hashed)


@router.post("/register", response_model=Token)
def register(data: UserCreate, session: Session = Depends(get_session)):
    user_exists = session.exec(select(User).where(User.email == data.email)).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=data.email, password_hash=get_password_hash(data.password), name=data.name)
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token(str(user.id))
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(data: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(str(user.id))
    return Token(access_token=token)
