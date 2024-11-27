# SpeechToTextAI-be

Run locally:
- Fill in .env for backend
- Run Backend then Frontend separately, in separate terminals
- Then access Frontend via localhost

Frontend
- cd frontend/
- npm install
- npm run dev

Backend
- cd backend/
- source venv/bin/activate   
- python3 main.py
- deactivate

Switch language
- Go to backend/main.py
- Comment out "language" variable, and uncomment another "language" variable next to it


In Window Powershell:
- May need to use py as cmd instead of python3
- Different venv startup