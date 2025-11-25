@echo off
echo Installing IdleDuelist Dependencies...
echo.
echo This script will install dependencies using pre-built packages
echo to avoid needing Rust/Cargo compilation.
echo.

REM Try to find Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :install
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py
    goto :install
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3
    goto :install
)

echo ERROR: Python not found!
pause
exit /b 1

:install
echo Found Python, starting installation...
echo.

REM Upgrade pip first
echo [1/3] Upgrading pip...
%PYTHON_CMD% -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo Failed to upgrade pip
    pause
    exit /b 1
)

REM Install bcrypt separately first (most likely to need special handling)
echo.
echo [2/3] Installing bcrypt (this may take a moment)...
%PYTHON_CMD% -m pip install bcrypt --no-build-isolation
if %ERRORLEVEL% NEQ 0 (
    echo Warning: bcrypt installation had issues, but continuing...
)

REM Install remaining packages (using latest versions for Python 3.14 compatibility)
echo.
echo [3/3] Installing remaining dependencies...
echo (Using latest versions for better Python 3.14 compatibility)
%PYTHON_CMD% -m pip install fastapi uvicorn[standard] pydantic python-multipart pytz --upgrade

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ All dependencies installed successfully!
    echo.
    echo You can now run: start_server.bat
) else (
    echo.
    echo ⚠️  Some packages may have failed to install.
    echo Try running: %PYTHON_CMD% -m pip install -r requirements.txt
)

echo.
pause

