@echo off
echo ========================================
echo CV Agent Pipeline - Web Interface
echo ========================================
echo.
echo Starting web server...
echo Open http://localhost:8000 in your browser
echo.
echo Press Ctrl+C to stop the server
echo.
python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000
