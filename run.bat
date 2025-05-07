@echo off
cd /d "%~dp0"

REM Activate virtual environment (adjust path if needed)
call venv\Scripts\activate

REM Run the script
python dmacontrol.py

pause
