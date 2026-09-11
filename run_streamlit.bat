@echo off
title SatQuery AI - Streamlit Dashboard
echo ===================================================
echo        SatQuery AI - Streamlit Web Server
echo ===================================================
echo.
echo Launching Streamlit on http://localhost:8501...
echo.
streamlit run streamlit_app.py --server.port 8501
pause
