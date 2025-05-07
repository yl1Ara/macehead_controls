@echo off
cd /d "%~dp0"

echo Checking for Python installation...
where python >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Python not found!
    echo Downloading latest Python installer...
    powershell -Command "Start-Process 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe'"
    echo.
    echo Please install Python with 'Add to PATH' checked, then re-run this script.
    pause
    exit /b
)

echo Python is available.
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing required packages from reqs.txt...
pip install -r reqs.txt

echo.
echo [Step 5] Checking NI-DAQmx availability in Python...
python -c "import nidaqmx; print('NI-DAQmx Python module loaded.'); print('Devices:', list(nidaqmx.system.System.local().devices))" 2>nul
if %errorlevel% NEQ 0 (
    echo NI-DAQmx not working or not installed.
    echo Opening NI-DAQmx driver download page...
    start https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html#565026
    echo.
    echo Please install NI-DAQmx and re-run this script if needed.
)

echo Done! You can now run your GUI with run.bat
pause
