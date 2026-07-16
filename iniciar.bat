@echo off
cd /d "%~dp0"

if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo No encontre el entorno virtual todavia. Preparandolo (puede tardar un minuto)...
    python enzo.py
    if errorlevel 1 (
        echo.
        echo Algo fallo preparando el entorno. Revisa que Python este instalado y en el PATH.
        pause
        exit /b 1
    )
)

start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0launcher.py"
