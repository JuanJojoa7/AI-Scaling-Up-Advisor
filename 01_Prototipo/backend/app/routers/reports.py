import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from typing import Dict, Any
from datetime import datetime
import os

from ..security import get_current_user
from ..database import get_session, Crypto
from ..models import DiagSession, Answer, Report
from ..llm import generate_insights
from ..scoring import compute_scores
from ..pdf import create_pdf, OUTPUT_DIR

router = APIRouter()
@router.post("/summary")
def summary(data: Dict[str, Any], user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Devuelve un resumen compacto sin generar PDF ni completar la sesión."""
    session_id = int(data.get("session_id"))
    s = session.exec(select(DiagSession).where(DiagSession.id == session_id, DiagSession.user_id == user.id)).first()
    if not s:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    ans = session.exec(select(Answer).where(Answer.session_id == s.id)).all()
    answers = []
    notes = []
    for a in ans:
        val = Crypto.decrypt(a.raw_value)
        try:
            val = json.loads(val) if isinstance(val, str) else val
        except Exception:
            pass
        answers.append({"module": a.module, "question_id": a.question_id, "value": val})
        if isinstance(val, str) and len(val.strip()) > 0:
            notes.append(val.strip()[:200])
    with open("backend/app/question_bank.json", "r", encoding="utf-8") as f:
        qlist = json.load(f)
    qmap = {q["id"]: q for q in qlist}
    scores = compute_scores(answers, qmap)
    insights = generate_insights(scores, notes)
    # Resumen compacto (1-2 frases + top 3 bullets)
    compact = insights["narrative"]
    if len(compact) > 360:
        compact = compact[:360].rsplit(" ", 1)[0] + "…"
    return {
        "scores": scores,
        "summary": compact,
        "priorities": insights.get("priorities", [])[:3],
        "recommendations": insights.get("recommendations", [])[:3],
    }



@router.post("/generate")
def generate(data: Dict[str, Any], user=Depends(get_current_user), session: Session = Depends(get_session)):
    session_id = int(data.get("session_id"))
    s = session.exec(select(DiagSession).where(DiagSession.id == session_id, DiagSession.user_id == user.id)).first()
    if not s:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    ans = session.exec(select(Answer).where(Answer.session_id == s.id)).all()
    answers = []
    notes = []
    for a in ans:
        val = Crypto.decrypt(a.raw_value)
        try:
            val = json.loads(val) if isinstance(val, str) else val
        except Exception:
            pass
        answers.append({"module": a.module, "question_id": a.question_id, "value": val})
        if isinstance(val, str) and len(val.strip()) > 0:
            notes.append(val.strip()[:200])
    # load questions
    with open("backend/app/question_bank.json", "r", encoding="utf-8") as f:
        qlist = json.load(f)
    qmap = {q["id"]: q for q in qlist}
    scores = compute_scores(answers, qmap)
    insights = generate_insights(scores, notes)
    # Quitar duplicados visibles
    def _dedup(items):
        seen=set(); out=[]
        for it in items:
            k=it.strip()
            if k and k not in seen:
                seen.add(k); out.append(k)
        return out
    pr = _dedup(insights["priorities"])[:3]
    rec = _dedup(insights["recommendations"])[:10]
    pdf_path = create_pdf(s.id, scores, insights["narrative"], pr, rec)

    report = Report(
        session_id=s.id,
        scores_json=json.dumps(scores, ensure_ascii=False),
        narrative=insights["narrative"],
    priorities_json=json.dumps(pr, ensure_ascii=False),
    recommendations_json=json.dumps(rec, ensure_ascii=False),
        resources_json=json.dumps([
            "Growth Institute Scaling Up Program",
            "Mentoría especializada en BHAG",
            "Workshop de KPIs y ejecución disciplinada",
        ], ensure_ascii=False),
    radar_image_path="",
    )
    session.add(report)
    s.status = "completed"
    s.updated_at = datetime.utcnow()
    session.add(s)
    session.commit()

    return {
        "session_id": s.id,
        "scores": scores,
        "narrative": insights["narrative"],
    "priorities": pr,
    "recommendations": rec,
        "pdf_url": f"/api/reports/pdf/{s.id}",
    }


@router.get("/pdf/{session_id}")
def download_pdf(session_id: int):
    path = os.path.join(OUTPUT_DIR, f"report_{session_id}.pdf")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    return FileResponse(path, media_type="application/pdf", filename=f"ScalingUp_Report_{session_id}.pdf")
