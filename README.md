# AI Scaling Up Advisor

Herramienta web (Python + FastAPI + Frontend estático) que guía a líderes de pymes a través de un diagnóstico inspirado en la metodología *Scaling Up* (People, Strategy, Execution, Cash) y genera un informe con puntajes, prioridades y recomendaciones empleando un modelo LLM (Groq API).

## Características

- Onboarding explicativo de las 4 decisiones.
- Preguntas guiadas por módulo (People, Strategy, Execution, Cash) en formato texto, número y selección múltiple.
- Cálculo de puntajes 0–10 por área (normalización simple y ponderación por "weight").
- Generación de diagnóstico narrativo + Top 3 prioridades + recomendaciones accionables usando Groq LLM.
- Registro/Login con JWT (almacenamiento SQLite) y posibilidad de reanudar sesiones.
- Campos de respuestas cifrados opcionalmente con Fernet.
- Arquitectura extensible: preguntas en question_bank.json.

## Requisitos Previos

- Python 3.11+
- Una cuenta y API Key de Groq.

## Instalación (Windows PowerShell)

powershell
cd c:\Ruta\A\AI-Scaling-Up-Advisor
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt


## Variables de Entorno

Es necesario crear un archivo .env en shell antes de ejecutar:

powershell
$env:GROQ_API_KEY="TU_API_KEY_GROQ_AQUI"  
$env:GROQ_MODEL="llama-3.1-8b-instant" #Modelo preferido por su ratio costo/beneficio.
$env:JWT_SECRET="secreto"
# Es necesario generar una clave Fernet para el cifrado mencionado anteriormente, usando el siguiente comando:
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`


$env:DATA_ENCRYPTION_KEY="CLAVE_FERNET_GENERADA"


## Ejecutar Backend

powershell
uvicorn backend.app.main:app --reload --port 8000


## Abrir Frontend

Abre frontend/index.html en el navegador. El frontend llama al backend en http://127.0.0.1:8000.

## Flujo de Uso

1. Registrar o iniciar sesión.
2. Leer onboarding y comenzar diagnóstico.
3. Responder preguntas. Al terminar se muestra un resumen del informe.
4. Generar informe final: se consulta Groq, se crea PDF y se muestran prioridades/recomendaciones.
5. Descargar PDF.

## Extender Preguntas

Edita backend/app/question_bank.json agregando objetos con campos:

json
{ "id": "e3", "module": "execution", "text": "Nueva pregunta", "type": "text", "weight": 1, "min_chars": 40 }


Tipos soportados:
- text (usa min_chars para puntaje completo)
- number (usa min y max para normalizar)
- multi (lista options y best para la opción ideal)

# AI Scaling Up Advisor
