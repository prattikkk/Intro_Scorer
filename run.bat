@echo off
echo ========================================
echo   NIRMAAN AI STUDENT SCORER
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo.
echo Starting application...
echo Open: http://localhost:5000
echo.
python app.py
