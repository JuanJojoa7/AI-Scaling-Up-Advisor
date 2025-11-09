import os
from typing import List, Dict

try:
    from groq import Groq
except Exception:
    Groq = None
import requests

class GroqAPIError(Exception):
    pass

GROQ_API_KEY_ENV = "GROQ_API_KEY"


SYSTEM_PROMPT = (
    "Eres un asesor ejecutivo experto en 'Scaling Up' (Verne Harnish). "
    "Recibirás puntajes en People, Strategy, Execution y Cash (0-10) más notas del usuario. "
    "Genera: (1) diagnóstico narrativo claro y empático, (2) top 3 prioridades, "
    "(3) recomendaciones accionables por prioridad, usando lenguaje sencillo y concreto. "
    "Sé breve pero sustancial."
)


def _groq_sdk_client():
    api_key = os.getenv(GROQ_API_KEY_ENV)
    if not api_key:
        raise RuntimeError("GROQ_API_KEY no configurada")
    if Groq is not None:
        try:
            # Newer groq SDK may not accept extra params; keep minimal
            return Groq(api_key=api_key)
        except TypeError:
            # Fallback: force REST path by returning None
            return None
    return None


def generate_insights(scores: Dict[str, float], notes: List[str]) -> Dict[str, object]:
    prompt = (
        f"Puntajes -> People: {scores.get('people', 0)}, Strategy: {scores.get('strategy', 0)}, "
        f"Execution: {scores.get('execution', 0)}, Cash: {scores.get('cash', 0)}.\n"
        f"Notas del usuario (resúmenes):\n- " + "\n- ".join(notes[:8])
    )

    client = _groq_sdk_client()
    if client:
        resp = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )
        text = resp.choices[0].message.content.strip()
    else:
        # Fallback to REST if SDK not available
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv(GROQ_API_KEY_ENV)}",
            "Content-Type": "application/json",
        }
        data = {
            "model": os.getenv("GROQ_MODEL", "llama3-8b-8192"),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.6,
        }
        r = requests.post(url, headers=headers, json=data, timeout=30)
        if r.status_code >= 400:
            # Return graceful fallback text instead of raising
            return {
                "narrative": "No se pudo obtener respuesta del modelo en este momento. Usa los puntajes para priorizar: enfócate primero en las áreas más bajas, define metas trimestrales claras y establece un ritmo de reuniones semanal con KPIs visibles.",
                "priorities": ["Priorizar áreas débiles","Definir metas trimestrales","Establecer ritmo de ejecución"],
                "recommendations": [
                    "Revisa preguntas con puntaje bajo y redacta acciones concretas para cada una.",
                    "Define 3 objetivos trimestrales medibles alineados al BHAG.",
                    "Implementa reunión semanal con agenda fija y seguimiento de KPIs.",
                ],
            }
        text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip() or "Sin contenido del modelo."  

    # Parse and clean
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    raw_priorities: List[str] = []
    raw_recos: List[str] = []
    body_lines: List[str] = []
    for ln in lines:
        low = ln.lower().lstrip("- *")
        if low.startswith("top 3") or low.startswith("prioridades") or low.startswith("recomendaciones"):
            continue
        if low.startswith(("1.", "2.", "3.", "prioridad")):
            raw_priorities.append(ln.lstrip("- *"))
            continue
        if low.startswith("- ") or "recom" in low or "implementar" in low or "definir" in low:
            raw_recos.append(ln.lstrip("- *"))
            continue
        body_lines.append(ln)

    def _dedup(seq: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for s in seq:
            k = s.strip()
            if k and k not in seen:
                seen.add(k)
                out.append(k)
        return out

    priorities = _dedup(raw_priorities)[:3] or [
        "Definir/afinar BHAG", "Implementar dashboard de KPIs", "Mejorar ciclo de efectivo"
    ]
    recommendations = _dedup(raw_recos)[:6] or [
        "Clarificar y comunicar BHAG y propuesta de valor en una página",
        "Establecer ritmo semanal con 3-5 KPIs críticos visibles",
        "Optimizar términos de cobro/pago para reducir días en efectivo",
    ]
    narrative = "\n".join(body_lines) or text
    return {"narrative": narrative, "priorities": priorities, "recommendations": recommendations}
