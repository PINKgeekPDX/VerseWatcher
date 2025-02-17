@echo off
setlocal enabledelayedexpansion

:: Change to script directory
cd /d "%~dp0"

:: Check if running from source or executable
if exist "dist\VerseWatcher.exe" (
    :: Run the executable version silently
    start "" "dist\VerseWatcher.exe"
    exit /b 0
)

:: Check for Python virtual environment and set paths
if exist "venv\Scripts\activate.bat" (
    :: Activate venv silently and set Python path
    call "venv\Scripts\activate.bat" >nul 2>&1
    set "PYTHON_PATH=!VIRTUAL_ENV!\Scripts\pythonw.exe"
) else (
    :: Use system Python if no venv
    where pythonw.exe >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_PATH=pythonw.exe"
    ) else (
        echo Python is not installed or not in PATH
        echo Please install Python 3.8 or higher
        pause
        exit /b 1
    )
)

:: Check Python installation silently
"%PYTHON_PATH%" --version >nul 2>&1
if !errorlevel! neq 0 (
    echo Error: Python check failed
    echo Please ensure Python 3.8 or higher is installed
    pause
    exit /b 1
)

:: Check dependencies silently
pip show PyQt5 >nul 2>&1
if !errorlevel! neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt >nul 2>&1
    if !errorlevel! neq 0 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

:: Start the application without console window
start "" /wait "%PYTHON_PATH%" src/main.py

endlocal 