"""Herramienta para generar resultados.xlsx consolidado.

Hojas:
  Sesiones: id, user_email, status, created_at, updated_at, respuestas, tiene_reporte
  Respuestas: session_id, question_id, module, valor (desencriptado), timestamp
  Reportes: session_id, people, strategy, execution, cash, prioridades, recomendaciones, narrativa (truncada)
  Metricas: total_usuarios, total_sesiones, sesiones_completadas, promedio_respuestas_por_sesion, tiempo_generacion (placeholder), fecha_exportacion

Uso:
  python -m backend.app.export_results

Requiere que la base advisor.db exista y DATA_ENCRYPTION_KEY si se usó cifrado.
"""

import os
import json
from datetime import datetime
from typing import List
from sqlmodel import Session, select
from .database import engine, Crypto
from .models import User, DiagSession, Answer, Report

try:
    import openpyxl  # preferred
    from openpyxl import Workbook
except ImportError:
    raise RuntimeError("Instala openpyxl para exportar: pip install openpyxl")

EXPORT_FILENAME = "resultados.xlsx"


def _safe_decrypt(raw: str) -> str:
    try:
        return Crypto.decrypt(raw) or ""
    except Exception:
        return raw


def export():
    wb = Workbook()
    ws_sessions = wb.active
    ws_sessions.title = "Sesiones"
    ws_answers = wb.create_sheet("Respuestas")
    ws_reports = wb.create_sheet("Reportes")
    ws_metrics = wb.create_sheet("Metricas")

    with Session(engine) as session:
        users = {u.id: u for u in session.exec(select(User)).all()}
        sessions: List[DiagSession] = session.exec(select(DiagSession)).all()
        answers: List[Answer] = session.exec(select(Answer)).all()
        reports: List[Report] = session.exec(select(Report)).all()
        report_by_session = {r.session_id: r for r in reports}

    # Sesiones
    ws_sessions.append(["id", "user_email", "status", "created_at", "updated_at", "respuestas", "tiene_reporte"])
    for s in sessions:
        ws_sessions.append([
            s.id,
            users.get(s.user_id).email if users.get(s.user_id) else "?",
            s.status,
            s.created_at.isoformat(),
            s.updated_at.isoformat(),
            sum(1 for a in answers if a.session_id == s.id),
            1 if s.id in report_by_session else 0,
        ])

    # Respuestas
    ws_answers.append(["session_id", "question_id", "module", "valor", "timestamp"])
    for a in answers:
        ws_answers.append([
            a.session_id,
            a.question_id,
            a.module,
            _safe_decrypt(a.raw_value),
            a.created_at.isoformat(),
        ])

    # Reportes
    ws_reports.append(["session_id", "people", "strategy", "execution", "cash", "prioridades", "recomendaciones", "narrativa_truncada"])
    for r in reports:
        try:
            scores = json.loads(r.scores_json)
        except Exception:
            scores = {}
        try:
            pr = json.loads(r.priorities_json)
        except Exception:
            pr = []
        try:
            rec = json.loads(r.recommendations_json)
        except Exception:
            rec = []
        narr = (r.narrative or "")[:400].replace("\n", " ")
        ws_reports.append([
            r.session_id,
            scores.get("people"),
            scores.get("strategy"),
            scores.get("execution"),
            scores.get("cash"),
            "; ".join(pr),
            "; ".join(rec),
            narr,
        ])

    # Métricas
    total_usuarios = len(users)
    total_sesiones = len(sessions)
    sesiones_completadas = sum(1 for s in sessions if s.status == "completed")
    promedio_respuestas = round(len(answers) / total_sesiones, 2) if total_sesiones else 0
    ws_metrics.append(["metrica", "valor"])
    ws_metrics.append(["total_usuarios", total_usuarios])
    ws_metrics.append(["total_sesiones", total_sesiones])
    ws_metrics.append(["sesiones_completadas", sesiones_completadas])
    ws_metrics.append(["promedio_respuestas_por_sesion", promedio_respuestas])
    ws_metrics.append(["fecha_exportacion", datetime.utcnow().isoformat()])
    ws_metrics.append(["version_modelo_llm", os.getenv("GROQ_MODEL", "llama3-8b-8192")])

    wb.save(EXPORT_FILENAME)
    return EXPORT_FILENAME


if __name__ == "__main__":
    fname = export()
    print(f"Exportado: {fname}")