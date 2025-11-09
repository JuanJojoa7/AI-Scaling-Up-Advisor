# AI Scaling Up Advisor

Herramienta web (Python + FastAPI + Frontend estático) que guía a líderes de pymes a través de un diagnóstico inspirado en la metodología **Scaling Up** (People, Strategy, Execution, Cash) y genera un informe con puntajes, prioridades y recomendaciones empleando un modelo LLM (Groq API).

## Características

- Onboarding explicativo de las 4 decisiones.
- Preguntas guiadas por módulo (People, Strategy, Execution, Cash) en formato texto, número y selección múltiple.
- Cálculo de puntajes 0–10 por área (normalización simple y ponderación por "weight").
- Generación de diagnóstico narrativo + Top 3 prioridades + recomendaciones accionables usando Groq LLM.
- Gráfico radar y exportación PDF del "Scaling Up Health Report".
- Registro/Login con JWT (almacenamiento SQLite) y posibilidad de reanudar sesiones.
- Campos de respuestas cifrados opcionalmente con Fernet (si defines la clave).
- Arquitectura extensible: preguntas en `question_bank.json`.

## Requisitos Previos

- Python 3.11+
- Una cuenta y API Key de Groq (ya la tienes). No compartas tu API key públicamente.

## Instalación (Windows PowerShell)

```powershell
cd c:\Universidad\OctavoSemestre\IA2\ProyectoFinal\AI-Scaling-Up-Advisor
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Variables de Entorno

Crea un archivo `.env` (opcional) o exporta en tu shell antes de ejecutar:

```powershell
$env:GROQ_API_KEY="TU_API_KEY_GROQ_AQUI"  # NO la subas a git
$env:GROQ_MODEL="llama3-8b-8192"          # modelo por defecto
$env:JWT_SECRET="cambia-este-secreto"
# Genera una clave Fernet si quieres cifrar (opcional):
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
$env:DATA_ENCRYPTION_KEY="CLAVE_FERNET_GENERADA"
```

## Ejecutar Backend

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

## Abrir Frontend

Abre `frontend/index.html` en tu navegador (o sirve con alguna extensión Live Server). El frontend llama al backend en `http://127.0.0.1:8000`.

## Flujo de Uso

1. Registrar o iniciar sesión.
2. Leer onboarding y comenzar diagnóstico.
3. Responder preguntas. Al terminar se muestran puntajes preliminares (radar chart).
4. Generar informe final: se consulta Groq, se crea PDF y se muestran prioridades/recomendaciones.
5. Descargar PDF.

## Extender Preguntas

Edita `backend/app/question_bank.json` agregando objetos con campos:

```json
{ "id": "e3", "module": "execution", "text": "Nueva pregunta", "type": "text", "weight": 1, "min_chars": 40 }
```

Tipos soportados:
- `text` (usa `min_chars` para puntaje completo)
- `number` (usa `min` y `max` para normalizar)
- `multi` (lista `options` y `best` para la opción ideal)

## Seguridad Básica

- Usa HTTPS en despliegue (aquí es desarrollo local).
- No expongas ni subas tu API Key Groq.
- Cambia `JWT_SECRET` en producción.
- Cifra respuestas con `DATA_ENCRYPTION_KEY`.

## Próximos Pasos (Mejoras sugeridas)

- Endpoint real de descarga PDF (enviar archivo en vez de path JSON).
- Más preguntas y pesos calibrados con coaches.
- Panel histórico de reportes por usuario.
- Internacionalización.
- Deploy en Azure / Render / Railway con base de datos Postgres.

## Licencia

Uso académico / demostración.
# AI Scaling Up Advisor

