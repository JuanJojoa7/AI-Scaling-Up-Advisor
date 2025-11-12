import os
from sqlmodel import SQLModel, create_engine, Session
from cryptography.fernet import Fernet
from typing import Optional

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./advisor.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})

# Simple field-level encryption for sensitive fields
_ENC_KEY_ENV = "DATA_ENCRYPTION_KEY"

class Crypto:
    _fernet: Optional[Fernet] = None

    @classmethod
    def get_fernet(cls) -> Optional[Fernet]:
        if cls._fernet is not None:
            return cls._fernet
        key = os.getenv(_ENC_KEY_ENV)
        if key:
            try:
                cls._fernet = Fernet(key.encode())
            except Exception:
                cls._fernet = None
        return cls._fernet

    @classmethod
    def encrypt(cls, data: Optional[str]) -> Optional[str]:
        if data is None:
            return None
        f = cls.get_fernet()
        if not f:
            return data
        return f.encrypt(data.encode()).decode()

    @classmethod
    def decrypt(cls, data: Optional[str]) -> Optional[str]:
        if data is None:
            return None
        f = cls.get_fernet()
        if not f:
            return data
        try:
            return f.decrypt(data.encode()).decode()
        except Exception:
            return data


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
