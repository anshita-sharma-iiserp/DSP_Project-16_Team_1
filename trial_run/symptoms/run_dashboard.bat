@echo off
echo Starting the COVID-19 Symptoms Knowledge Flow Dashboard...
echo Make sure you have installed the requirements using: pip install -r requirements.txt
echo.

cd trial_run\symptoms\notebooks
python -m streamlit run step6_dashboard.py

pause
