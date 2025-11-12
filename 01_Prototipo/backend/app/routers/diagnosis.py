import json
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
# removed unused import 'col'
from typing import List, Dict, Any
from datetime import datetime

from ..security import get_current_user
from ..database import get_session, Crypto
from ..models import DiagSession, Answer
from ..schemas import Question, AnswerIn
from ..scoring import compute_scores

router = APIRouter()

# Load question bank once
with open("backend/app/question_bank.json", "r", encoding="utf-8") as f:
    QUESTION_LIST: List[Dict[str, Any]] = json.load(f)
QUESTION_MAP = {q["id"]: q for q in QUESTION_LIST}


@router.get("/onboarding")
def onboarding():
    return {
        "intro": "Soy tu AI Scaling Up Advisor. Juntos haremos un diagnóstico rápido basado en 4 decisiones: People, Strategy, Execution y Cash.",
        "steps": [
            "Responderás preguntas breves (texto, selección o número)",
            "Al final recibirás un informe personalizado con puntajes, prioridades y recomendaciones",
        ],
    }


@router.post("/start")
def start_session(user=Depends(get_current_user), session: Session = Depends(get_session)):
    s = DiagSession(user_id=user.id, current_module="people")
    session.add(s)
    session.commit()
    session.refresh(s)
    return {"session_id": s.id}


@router.get("/sessions")
def list_sessions(user=Depends(get_current_user), session: Session = Depends(get_session)):
    sessions = session.exec(select(DiagSession).where(DiagSession.user_id == user.id).order_by(DiagSession.created_at.desc())).all()
    result = []
    for s in sessions:
        # Efficient count using SQL COUNT(*)
        answers_count = session.exec(select(Answer).where(Answer.session_id == s.id)).all()
        answers_total = len(answers_count)
        result.append({
            "id": s.id,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
            "answers_count": answers_total,
            "has_report": s.status == "completed"
        })
    return {"sessions": result}


@router.get("/questions", response_model=List[Question])
def get_questions():
    return QUESTION_LIST


@router.post("/answer")
def submit_answer(data: AnswerIn, user=Depends(get_current_user), session: Session = Depends(get_session)):
    s = session.exec(select(DiagSession).where(DiagSession.id == data.session_id, DiagSession.user_id == user.id)).first()
    if not s:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    raw = json.dumps(data.value, ensure_ascii=False)
    enc = Crypto.encrypt(raw)
    a = Answer(session_id=s.id, module=data.module, question_id=data.question_id, raw_value=enc or raw)
    s.updated_at = datetime.utcnow()
    session.add(a)
    session.add(s)
    session.commit()
    return {"ok": True}


@router.get("/resume/{session_id}")
def resume(session_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    s = session.exec(select(DiagSession).where(DiagSession.id == session_id, DiagSession.user_id == user.id)).first()
    if not s:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    ans = session.exec(select(Answer).where(Answer.session_id == s.id)).all()
    answers = []
    for a in ans:
        val = Crypto.decrypt(a.raw_value)
        try:
            val = json.loads(val) if isinstance(val, str) else val
        except Exception:
            pass
        answers.append({"module": a.module, "question_id": a.question_id, "value": val})
    return {"status": s.status, "answers": answers}


@router.post("/score")
def score(data: Dict[str, Any], user=Depends(get_current_user), session: Session = Depends(get_session)):
    session_id = int(data.get("session_id"))
    s = session.exec(select(DiagSession).where(DiagSession.id == session_id, DiagSession.user_id == user.id)).first()
    if not s:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    # Answers can be sent from client or read from DB
    answers = data.get("answers")
    if answers is None:
        ans = session.exec(select(Answer).where(Answer.session_id == s.id)).all()
        answers = []
        for a in ans:
            val = Crypto.decrypt(a.raw_value)
            try:
                val = json.loads(val) if isinstance(val, str) else val
            except Exception:
                pass
            answers.append({"module": a.module, "question_id": a.question_id, "value": val})
    scores = compute_scores(answers, QUESTION_MAP)
    return {"scores": scores}
