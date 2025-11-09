import os
from typing import Dict, List
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

PROJECT_REPORTS_DIR = r"C:\Universidad\OctavoSemestre\IA2\ProyectoFinal\AI-Scaling-Up-Advisor\reports"
# Allow env override but default to fixed absolute path requested
OUTPUT_DIR = os.getenv("REPORTS_DIR", PROJECT_REPORTS_DIR)
try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
except Exception:
    # Fallback to relative if absolute path fails
    OUTPUT_DIR = "./reports"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
def create_pdf(session_id: int, scores: Dict[str, float], narrative: str, priorities: List[str], recommendations: List[str]) -> str:
    pdf_path = os.path.join(OUTPUT_DIR, f"report_{session_id}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # Título y cabecera
    y = height - 2*cm
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2*cm, y, "Reporte Ejecutivo Scaling Up")
    y -= 0.9*cm
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, y, f"Sesión: {session_id}")
    y -= 1.2*cm

    # Puntajes en una línea
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Puntajes (0-10):")
    y -= 0.6*cm
    c.setFont("Helvetica", 11)
    score_line = "  |  ".join([f"People: {scores.get('people',0):.1f}",
                                f"Strategy: {scores.get('strategy',0):.1f}",
                                f"Execution: {scores.get('execution',0):.1f}",
                                f"Cash: {scores.get('cash',0):.1f}"])
    c.drawString(2*cm, y, score_line)
    y -= 1.0*cm

    # Diagnóstico narrativo
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Diagnóstico narrativo:")
    y -= 0.5*cm
    c.setFont("Helvetica", 11)
    y = _write_wrapped(c, 2*cm, y, _clean_narrative(narrative), width_chars=95)
    y -= 0.4*cm

    # Top 3 Prioridades
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Top 3 Prioridades:")
    y -= 0.5*cm
    c.setFont("Helvetica", 11)
    for i, p in enumerate(_dedup(priorities)[:3], 1):
        y = _write_wrapped(c, 2.2*cm, y, f"{i}. {p}", width_chars=92)
        y -= 0.2*cm

    # Recomendaciones
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Recomendaciones:")
    y -= 0.5*cm
    c.setFont("Helvetica", 11)
    for r in _dedup(recommendations)[:10]:
        y = _write_wrapped(c, 2.2*cm, y, f"• {r}", width_chars=92)
        y -= 0.1*cm

    c.save()
    return pdf_path


def _wrap_text(text: str, width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) > width:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len += len(w) + (1 if cur_len > 0 else 0)
    if cur:
        lines.append(" ".join(cur))
    return lines


def _write_wrapped(c: canvas.Canvas, x: float, y: float, text: str, width_chars: int = 95, bottom_margin: float = 2*cm) -> float:
    """Write wrapped text with automatic page breaks. Returns the new y position."""
    width, height = A4
    for line in text.splitlines():
        for chunk in _wrap_text(line, width_chars):
            if y < bottom_margin:
                c.showPage()
                y = height - 2*cm
                c.setFont("Helvetica", 11)
            c.drawString(x, y, chunk)
            y -= 0.45*cm
    return y


def _dedup(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for it in items:
        k = it.strip()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _clean_narrative(text: str) -> str:
    # Remove headings and duplicate bullet sections often returned by LLM
    lines = []
    for ln in text.splitlines():
        l = ln.strip()
        low = l.lower()
        if not l:
            continue
        if low.startswith("top 3") or low.startswith("recomendaciones"):
            continue
        if low[:2].isdigit() or low.startswith("1.") or low.startswith("2.") or low.startswith("3."):
            # skip enumerated bullets inside narrative
            continue
        lines.append(l)
    return "\n".join(lines)
