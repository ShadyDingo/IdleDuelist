@echo off
echo Starting IdleDuelist Web Server...
echo.

REM Try to find Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Found Python, starting server...
    python start_server.py
    goto :end
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Found Python launcher, starting server...
    py start_server.py
    goto :end
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Found Python3, starting server...
    python3 start_server.py
    goto :end
)

echo.
echo ERROR: Python not found!
echo.
echo Please install Python 3.7 or higher from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo.
echo Alternatively, if Python is installed, try running manually:
echo   python start_server.py
echo   OR
echo   py start_server.py
echo.

:end
pause

