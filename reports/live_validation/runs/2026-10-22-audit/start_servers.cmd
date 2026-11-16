@echo off
rem Starts the live backend (127.0.0.1:8000) and the frontend dev server (127.0.0.1:5173) in two windows.
rem Close both windows to stop them. TESTING is cleared so the backend uses real models.
cd /d "%~dp0..\..\..\.."
set TESTING=
start "Medical RAG backend :8000" cmd /k ".venv\Scripts\python.exe -m uvicorn --app-dir src adaptive_trust_medical_rag.api.app:app --host 127.0.0.1 --port 8000"
start "Medical RAG frontend :5173" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"
