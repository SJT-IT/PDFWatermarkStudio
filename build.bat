
@echo off
setlocal
title PDF Watermark Studio Builder

cd /d "%~dp0"

echo ==========================================
echo       PDF Watermark Studio Builder
echo ==========================================
echo.

REM Check Python launcher
where py >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python launcher was not found.
    echo Install Python 3.12 or 3.13 for Windows.
    echo https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

REM Select Python version
set "PYTHON_CMD="

py -3.13 --version >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3.13"

if not defined PYTHON_CMD (
    py -3.12 --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)

if not defined PYTHON_CMD (
    echo ERROR: Python 3.12 or 3.13 was not found.
    echo Install Python 3.12 or 3.13 and try again.
    pause
    exit /b 1
)

echo Using:
%PYTHON_CMD% --version
echo.

REM Verify the PyInstaller spec file
if not exist "PDFWatermarkStudio.spec" (
    echo ERROR: PDFWatermarkStudio.spec was not found.
    echo Place this BAT file beside the spec file.
    pause
    exit /b 1
)

REM Create virtual environment if needed
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :error
)

echo.
echo Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

echo.
echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install customtkinter pymupdf pyinstaller
if errorlevel 1 goto :error

echo.
echo Building the single-file application...
".venv\Scripts\python.exe" -m PyInstaller ^
    --noconfirm --clean PDFWatermarkStudio.spec

if errorlevel 1 goto :error

if not exist "dist\PDFWatermarkStudio.exe" (
    echo ERROR: The build finished but the EXE was not found.
    goto :error
)

echo.
echo ==========================================
echo BUILD COMPLETE!
echo ==========================================
echo.
echo Executable:
echo %CD%\dist\PDFWatermarkStudio.exe
echo.
pause
exit /b 0

:error
echo.
echo BUILD FAILED. Review the errors above.
pause
exit /b 1
