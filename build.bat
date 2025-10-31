@echo off
echo Building LM Arena Chat Application...
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed!
    pause
    exit /b 1
)

if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo.
echo Building executable with PyInstaller...
pyinstaller --onefile --windowed --name "LMArena-Chat" --icon=NONE chat_app.py
set build_status=%errorlevel%

call .venv\Scripts\deactivate.bat

if %build_status% equ 0 (
    echo.
    echo Build completed successfully!
    echo.
    echo Executable location: dist\LMArena-Chat.exe
    echo.
    echo To run the application:
    echo   dist\LMArena-Chat.exe
    pause
    exit /b 0
) else (
    echo.
    echo Build failed!
    pause
    exit /b 1
)
