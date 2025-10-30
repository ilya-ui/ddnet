@echo off
setlocal enabledelayedexpansion

REM Navigate to the directory containing this script
cd /d "%~dp0"

echo Installing required Python packages...
py -m pip install --upgrade pip
if errorlevel 1 goto install_failed
py -m pip install -r requirements.txt
if errorlevel 1 goto install_failed

echo.
echo Launching LMArena Gemini Proxy...
set "LMARENA_PROXY_NO_PAUSE=0"
set "PYTHONPATH=%~dp0src"
py -m lmarena_proxy.main
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE% EQU 0 (
    echo Proxy exited normally.
) else (
    echo Proxy exited with error code %EXIT_CODE%.
)

goto end

:install_failed
echo.
echo Failed to install Python dependencies. Please ensure Python and pip are available.
set "EXIT_CODE=%ERRORLEVEL%"

:end
echo.
pause
endlocal
exit /b %EXIT_CODE%
