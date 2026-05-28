@echo off
echo =====================================
echo   Komiko - Self-hosted Comics Server
echo =====================================
echo.

if "%~1"=="" (
    echo Usage: setup-windows.bat [install_dir]
    echo.
    echo Example:
    echo   setup-windows.bat C:\Komiko
    echo.
    echo This will:
    echo   1. Create a Python virtual environment
    echo   2. Install dependencies
    echo   3. Set up data directories
    echo   4. Create a start script
    echo.
    set /p INSTALL_DIR="Enter install directory (default C:\Komiko): "
) else (
    set INSTALL_DIR=%~1
)

if "%INSTALL_DIR%"=="" set INSTALL_DIR=C:\Komiko

echo Install directory: %INSTALL_DIR%
echo.

:: Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

python --version
echo.

:: Create directories
echo [1/5] Creating directories...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\data" mkdir "%INSTALL_DIR%\data"
if not exist "%INSTALL_DIR%\data\covers" mkdir "%INSTALL_DIR%\data\covers"
echo   Done.

:: Copy application files
echo [2/5] Copying application files...
SCRIPT_DIR=%~dp0
xcopy /E /I /Y "%SCRIPT_DIR%app" "%INSTALL_DIR%\app\"
copy /Y "%SCRIPT_DIR%config.py" "%INSTALL_DIR%\"
copy /Y "%SCRIPT_DIR%run.py" "%INSTALL_DIR%\"
copy /Y "%SCRIPT_DIR%requirements.txt" "%INSTALL_DIR%\"
echo   Done.

:: Create virtual environment
echo [3/5] Creating Python virtual environment...
python -m venv "%INSTALL_DIR%\venv"
echo   Done.

:: Install dependencies
echo [4/5] Installing dependencies (this may take a minute)...
"%INSTALL_DIR%\venv\Scripts\pip.exe" install --upgrade pip -q
"%INSTALL_DIR%\venv\Scripts\pip.exe" install -r "%INSTALL_DIR%\requirements.txt" -q
"%INSTALL_DIR%\venv\Scripts\pip.exe" install waitress -q
echo   Done.

:: Generate secret key
echo [5/5] Generating secret key...
for /f %%i in ('"%INSTALL_DIR%\venv\Scripts\python.exe" -c "import secrets; print(secrets.token_hex(32))"') do set SECRET=%%i
echo   Done.

:: Create start script
echo @echo off > "%INSTALL_DIR%\start.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%\start.bat"
echo set FLASK_ENV=production >> "%INSTALL_DIR%\start.bat"
echo set SECRET_KEY=%SECRET% >> "%INSTALL_DIR%\start.bat"
echo set KOMIKO_DATA_DIR=%INSTALL_DIR%\data >> "%INSTALL_DIR%\start.bat"
echo echo Starting Komiko on http://localhost:5000 >> "%INSTALL_DIR%\start.bat"
echo echo Press Ctrl+C to stop. >> "%INSTALL_DIR%\start.bat"
echo "%INSTALL_DIR%\venv\Scripts\waitress-serve.exe" --host=0.0.0.0 --port=5000 --threads=4 run:app >> "%INSTALL_DIR%\start.bat"

:: Create stop info
echo.
echo =====================================
echo   Komiko installed!
echo =====================================
echo.
echo   Directory:   %INSTALL_DIR%
echo   Data:         %INSTALL_DIR%\data
echo   Start:        Run %INSTALL_DIR%\start.bat
echo   URL:          http://localhost:5000
echo.
echo   To run as a Windows Service, consider using NSSM:
echo     nssm install Komiko "%INSTALL_DIR%\venv\Scripts\waitress-serve.exe"
echo     nssm set Komiko AppParameters "--host=0.0.0.0 --port=5000 --threads=4 run:app"
echo     nssm set Komiko AppDirectory "%INSTALL_DIR%"
echo     nssm set Komiko AppEnvironmentExtra FLASK_ENV=production SECRET_KEY=%SECRET% KOMIKO_DATA_DIR=%INSTALL_DIR%\data
echo     nssm start Komiko
echo.
pause