@echo off
setlocal enabledelayedexpansion

echo ===================================
echo    VerseWatcher Build Process
echo ===================================
echo.

:: Check for PowerShell
echo Checking requirements...
powershell -Command "exit" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PowerShell is required but not found.
    echo Please install PowerShell from: https://github.com/PowerShell/PowerShell/releases
    pause
    exit /b 1
)

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is required but not found.
    echo Please install Python 3.8 or later from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

set "ARGS="
if "%1"=="/?" goto :usage
if "%1"=="-?" goto :usage
if "%1"=="--help" goto :usage

:parse_args
if "%1"=="" goto :run
if /i "%1"=="clean" (
    set "ARGS=!ARGS! -Clean"
) else if /i "%1"=="force" (
    set "ARGS=!ARGS! -Force"
) else if /i "%1"=="debug" (
    set "ARGS=!ARGS! -DebugMode"
) else if /i "%1"=="skipSign" (
    set "ARGS=!ARGS! -SkipSign"
) else (
    echo Unknown argument: %1
    goto :usage
)
shift
goto :parse_args

:run
echo Starting build process...
echo This may take a few minutes. Please wait...
echo.

:: Create a marker file to indicate build is running
set "marker_file=%TEMP%\versewatcher_build_running_%RANDOM%.txt"
echo Running > "%marker_file%"

:: Start PowerShell script in a new window and wait for it
powershell -NoProfile -ExecutionPolicy Bypass -NoExit -Command "$Host.UI.RawUI.WindowTitle = 'VerseWatcher Build'; $scriptPath = Join-Path '%~dp0' 'build\tools\sign-and-build.ps1'; if (-not (Test-Path $scriptPath)) { Write-Host 'ERROR: PowerShell script not found at:' $scriptPath -ForegroundColor Red; Write-Host 'Please ensure the build/tools directory exists and contains sign-and-build.ps1' -ForegroundColor Red; pause; exit 1 } try { Write-Host 'Found script at:' $scriptPath; $result = & $scriptPath %ARGS%; $result | Out-File -FilePath '%marker_file%' -Encoding UTF8; Write-Host 'Build process completed. Press any key to continue...'; $host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown') | Out-Null } catch { Write-Host 'Error: ' $_.Exception.Message -ForegroundColor Red; @{ Success = $false; Error = $_.Exception.Message } | ConvertTo-Json | Out-File -FilePath '%marker_file%' -Encoding UTF8; Write-Host 'Error occurred. Press any key to continue...'; $host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown') | Out-Null }"

:: Wait a moment to ensure file is written
timeout /t 2 >nul

:: Read the result file
if not exist "%marker_file%" (
    echo ERROR: Build process was interrupted or failed to start.
    echo Please try running the script again with administrator rights.
    pause
    exit /b 1
)

:: Read JSON from marker file
set "json="
for /f "usebackq delims=" %%i in ("%marker_file%") do set "json=%%i"
del "%marker_file%" 2>nul

:: Parse the JSON (with error handling)
if "%json%"=="" (
    echo ERROR: Failed to get build result
    echo Please check if you have administrator rights.
    pause
    exit /b 1
)

:: Extract status and report path
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command ^
    "try { $json = '%json%' | ConvertFrom-Json; if ($json.Success) { 'SUCCESS' } else { 'FAILED' } } catch { 'FAILED' }"`) do set "status=%%i"

for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command ^
    "try { $json = '%json%' | ConvertFrom-Json; $json.ReportPath } catch { 'No report available' }"`) do set "report_path=%%i"

echo.
if "%status%"=="SUCCESS" (
    echo ===================================
    echo    Build completed successfully!
    echo ===================================
) else (
    echo ===================================
    echo       Build process failed!
    echo ===================================
)
echo.

if "%report_path%"=="No report found" (
    echo ERROR: Build report not found.
    echo Please check if the build process has proper permissions.
    pause
    exit /b 1
)

if "%report_path%"=="No report available" (
    echo ERROR: Unable to process build report.
    echo Please try running the script again with administrator rights.
    pause
    exit /b 1
)

:prompt
echo Would you like to view the build report?
echo.
echo A) Yes - Open the report
echo B) No - Close this window
echo.
choice /C AB /N /M "Enter your choice (A or B): "

if errorlevel 2 goto :end
if errorlevel 1 (
    start notepad.exe "%report_path%"
    timeout /t 2 >nul
    goto :end
)

:end
if "%status%"=="FAILED" (
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo.
    echo Press any key to exit...
    pause >nul
)
exit /b

:usage
echo VerseWatcher Build Script
echo.
echo This script will build VerseWatcher and create a signed executable.
echo Requirements:
echo   - PowerShell
echo   - Python 3.8 or later
echo.
echo Usage: %~nx0 [options]
echo Options:
echo   clean    - Clean all build artifacts before building
echo   force    - Force rebuild everything
echo   debug    - Enable debug mode for detailed output
echo   skipSign - Skip executable signing
echo.
echo Examples:
echo   %~nx0
echo   %~nx0 clean
echo   %~nx0 clean force
echo   %~nx0 debug skipSign
echo.
pause
exit /b 1
