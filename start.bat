@echo off
echo ============================================
echo   PROJECT 71 - AIOps Platform Startup
echo ============================================

echo [1/3] Starting Docker infrastructure...
docker-compose up -d
timeout /t 45 /nobreak

echo [2/3] Starting all Python components...
start cmd /k "cd /d C:\Users\ASUS\Desktop\project71 && venv\Scripts\activate && python data/simulate_telemetry.py"
start cmd /k "cd /d C:\Users\ASUS\Desktop\project71 && venv\Scripts\activate && python detection/detection_engine.py"
start cmd /k "cd /d C:\Users\ASUS\Desktop\project71 && venv\Scripts\activate && python rca/rca_engine.py"
start cmd /k "cd /d C:\Users\ASUS\Desktop\project71 && venv\Scripts\activate && python reporting/report_engine.py"
start cmd /k "cd /d C:\Users\ASUS\Desktop\project71 && venv\Scripts\activate && uvicorn api.main:app --reload --port 8000"

echo [3/3] Starting React Dashboard...
start cmd /k "cd /d C:\Users\ASUS\Desktop\project71\dashboard && npm start"

echo ============================================
echo   All components started!
echo   API Docs  : http://localhost:8000/docs
echo   Dashboard : http://localhost:3000
echo   Kafka UI  : http://localhost:8080
echo ============================================
pause