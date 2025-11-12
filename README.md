# AI Scaling Up Advisor

Aplicación web (FastAPI + Frontend estático) que guía a líderes a través de un diagnóstico basado en Scaling Up (People, Strategy, Execution, Cash), calcula puntajes 0–10 y genera un resumen rápido y un reporte ejecutivo en PDF usando un modelo LLM (Groq).

## Demo y navegación rápida
- Prototipo (código): `01_Prototipo/`
	- [Frontend](./01_Prototipo/frontend/index.html)
	- [Backend (código)](./01_Prototipo/backend/app/)
	- [Banco de preguntas](./01_Prototipo/backend/app/question_bank.json)
	- [Flujo de datos (imagen)](./01_Prototipo/flujo_datos.png)
	- [Reportes generados (ejemplos)](./01_Prototipo/reports/)
- Documentos del proyecto
	- [Ficha del reto empresarial (PDF)](./00_Ficha_Reto.pdf)
	- [Informe de experimentación y pruebas (PDF)](./02_Validacion/Informe_Experimentacion.pdf)
	- [Resultados consolidados (Excel)](./02_Validacion/resultados.xlsx)
	- [Informe final (PDF)](./03_Entrega_Final/Informe_Final.pdf)
	- [Presentación (PPTX)](./03_Entrega_Final/presentacion.pptx)
	- [Prompts usados](./01_Prototipo/prompts/Prompts.md)
	- Demo en video: [YouTube](https://youtu.be/nOwhXl9vfIo)
- Exportador a Excel: [export_results.py](./01_Prototipo/backend/app/export_results.py)

## Características principales
- Preguntas guiadas por módulo (texto, número, multi). Puntajes normalizados 0–10 por área.
- Resumen rápido vía `/api/reports/summary` y Reporte PDF ejecutivo via `/api/reports/generate` (sin gráfico, texto limpio y deduplicado).
- Registro/Login con JWT, sesiones persistentes y reanudables. Respuestas cifradas con Fernet (opcional).
- PDFs guardados por defecto en la carpeta de reportes del proyecto (ruta fija configurada en `pdf.py`).
- Exportación consolidada a `resultados.xlsx` (sesiones, respuestas, reportes y métricas).

## Requisitos previos
- Python 3.10+ (probado en 3.10 y 3.11).
- Cuenta de Groq y API Key.

## Puesta en marcha (Windows PowerShell)
Ejecutar desde la carpeta del prototipo para aislar el entorno.

```powershell
cd C:\Universidad\OctavoSemestre\IA2\ProyectoFinal\AI-Scaling-Up-Advisor\01_Prototipo

# 1) Crear y activar entorno
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3) Variables de entorno mínimas (en esta sesión PowerShell)
$env:GROQ_API_KEY = "TU_API_KEY_GROQ"
$env:GROQ_MODEL   = "llama-3.1-8b-instant" # o el que prefieras
$env:JWT_SECRET   = "secreto"
# Genera una Fernet key si quieres cifrar respuestas
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
$env:DATA_ENCRYPTION_KEY = "CLAVE_FERNET_GENERADA"

# 4) Levantar backend (recomendado usar -m para evitar issues del launcher)
python -m uvicorn backend.app.main:app --reload --port 8000
```

Luego abre el [frontend](./01_Prototipo/frontend/index.html) en el navegador. El frontend apunta a `http://127.0.0.1:8000`.

## Flujo de uso
1) Registrarte o iniciar sesión.  
2) Iniciar diagnóstico y responder preguntas.  
3) Ver “Resumen rápido”.  
4) Generar Reporte PDF (se abrirá en el navegador y se guardará en la carpeta configurada).  
5) Opcional: exportar resultados a Excel.

## Exportar resultados a Excel
Desde `01_Prototipo` (con la venv activa):

```powershell
python -m backend.app.export_results
```

Se generará `resultados.xlsx` con hojas: Sesiones, Respuestas, Reportes y Métricas (ver [02_Validacion/resultados.xlsx](./02_Validacion/resultados.xlsx)).

## Extender preguntas
Edita [`backend/app/question_bank.json`](./01_Prototipo/backend/app/question_bank.json) agregando objetos como:

```json
{ "id": "e3", "module": "execution", "text": "Nueva pregunta", "type": "text", "weight": 1, "min_chars": 40 }
```

Tipos soportados: 
- `text` (usa `min_chars` para puntaje completo)
- `number` (usa `min` y `max` para normalizar)
- `multi` (define `options` y `best` para la opción ideal)

## Endpoints (visión rápida)
- `POST /api/auth/register` · `POST /api/auth/login`
- `POST /api/diagnosis/start` · `GET /api/diagnosis/questions` · `POST /api/diagnosis/answer` · `GET /api/diagnosis/resume/{id}` · `GET /api/diagnosis/sessions`
- `POST /api/reports/summary` (resumen compacto) · `POST /api/reports/generate` (PDF) · `GET /api/reports/pdf/{id}`

## Solución de problemas
- “Unable to create process … uvicorn.exe”: usa `python -m uvicorn …` dentro de la venv de `01_Prototipo`, o reinstala uvicorn: `python -m pip install --force-reinstall "uvicorn[standard]==0.32.0"`.
- `ModuleNotFoundError: sqlmodel/openpyxl`: `pip install -r requirements.txt` (incluye `sqlmodel` y `openpyxl`).
- Groq 4xx/timeout: el sistema devuelve un fallback narrativo para no bloquear; reintenta más tarde.
- PDF: se guarda en la carpeta configurada en `backend/app/pdf.py`. Por defecto encontrarás archivos en [`01_Prototipo/reports/`](./01_Prototipo/reports/).

---

Hecho con FastAPI, JavaScript y Groq LLM. Pensado para portafolio y prácticas de Scaling Up.
