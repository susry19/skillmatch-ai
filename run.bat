@echo off
cd /d "%~dp0"
echo SkillMatch AI v4 baslatiliyor...
pip install -r backend/requirements.txt -q
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pause
