@echo off
setlocal enabledelayedexpansion
title Git Authentication Setup
color 0A

echo ========================================
echo Git Authentication Setup
echo ========================================
echo.
echo This script configures Git authentication for automatic pushes.
echo It will check for existing credentials and only set up if needed.
echo.

REM Check if git is available (check multiple locations)
set GIT_CMD=
where git >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set GIT_CMD=git
) else (
    REM Check common Git installation paths
    if exist "C:\Program Files\Git\bin\git.exe" (
        set GIT_CMD="C:\Program Files\Git\bin\git.exe"
    ) else if exist "C:\Program Files (x86)\Git\bin\git.exe" (
        set GIT_CMD="C:\Program Files (x86)\Git\bin\git.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Git\bin\git.exe" (
        set GIT_CMD="%LOCALAPPDATA%\Programs\Git\bin\git.exe"
    ) else (
        echo [ERROR] Git is not found in PATH or common installation locations!
        echo.
        echo Git appears to be installed (Git Bash found), but not accessible from PATH.
        echo.
        echo Option 1: Add Git to PATH
        echo   1. Right-click "This PC" ^> Properties ^> Advanced system settings
        echo   2. Click "Environment Variables"
        echo   3. Under "System variables", find "Path" and click "Edit"
        echo   4. Add: C:\Program Files\Git\bin
        echo   5. Click OK and restart Command Prompt
        echo.
        echo Option 2: Use Git Bash instead
        echo   - Open Git Bash from Start Menu
        echo   - Navigate to your project folder
        echo   - Run: scripts/setup_git_auth.bat
        echo.
        echo Option 3: Use the PowerShell script
        echo   - Open PowerShell
        echo   - Run: .\scripts\setup_git_auth.ps1
        echo.
        pause
        exit /b 1
    )
)

REM Check if we're in a git repository
if not exist .git (
    echo [ERROR] Not a git repository!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

echo [OK] Git repository detected
echo [OK] Using Git: %GIT_CMD%
echo.

REM Check for existing credentials
set CREDENTIALS_FILE=%USERPROFILE%\.git-credentials
if exist "%CREDENTIALS_FILE%" (
    echo [INFO] Found existing credentials file
    echo Checking if authentication works...
    %GIT_CMD% ls-remote --heads origin >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Existing credentials are working!
        echo No setup needed.
        echo.
        pause
        exit /b 0
    ) else (
        echo [WARNING] Existing credentials may be invalid or expired
        echo.
    )
)

REM Check if credential helper is configured
%GIT_CMD% config --global credential.helper >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Configuring Git credential helper...
    %GIT_CMD% config --global credential.helper store
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to configure credential helper
        pause
        exit /b 1
    )
    echo [OK] Credential helper configured
) else (
    echo [OK] Credential helper already configured
)

echo.
echo ========================================
echo Token Setup Required
echo ========================================
echo.
echo You need a GitHub Personal Access Token (PAT) with 'repo' permissions.
echo.
echo Option 1: Use existing token
echo   - If you already have a token, paste it when prompted
echo.
echo Option 2: Create new token
echo   1. Go to: https://github.com/settings/tokens
echo   2. Click "Generate new token (classic)"
echo   3. Name it: "IdleDuelist Auto-Push"
echo   4. Select scope: "repo" (Full control of private repositories)
echo   5. Click "Generate token"
echo   6. Copy the token (you'll only see it once!)
echo.
echo ========================================
echo.

set /p GITHUB_TOKEN="Enter your GitHub Personal Access Token: "

if "!GITHUB_TOKEN!"=="" (
    echo [ERROR] No token provided
    pause
    exit /b 1
)

REM Validate token format (GitHub tokens start with ghp_)
echo !GITHUB_TOKEN! | findstr /R "^ghp_" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Token doesn't match expected format (should start with 'ghp_')
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        exit /b 1
    )
)

echo.
echo Configuring credentials...

REM Get repository URL
for /f "tokens=*" %%i in ('%GIT_CMD% remote get-url origin 2^>nul') do set REPO_URL=%%i
if "!REPO_URL!"=="" (
    echo [ERROR] Could not find git remote URL
    pause
    exit /b 1
)

REM Create credentials file
echo https://!GITHUB_TOKEN!@github.com > "%CREDENTIALS_FILE%"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create credentials file
    pause
    exit /b 1
)

REM Set secure permissions (Windows)
icacls "%CREDENTIALS_FILE%" /inheritance:r /grant:r "%USERNAME%:R" >nul 2>&1

echo [OK] Credentials file created
echo.

REM Test the configuration
echo Testing authentication...
%GIT_CMD% ls-remote --heads origin >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Authentication successful!
    echo.
    echo ========================================
    echo [SUCCESS] Git authentication configured!
    echo ========================================
    echo.
    echo You can now use deploy.bat to automatically push to GitHub.
    echo.
) else (
    echo [ERROR] Authentication failed!
    echo.
    echo Possible issues:
    echo - Token may be invalid or expired
    echo - Token may not have 'repo' permissions
    echo - Network connection issue
    echo.
    echo Please verify your token at: https://github.com/settings/tokens
    echo.
    REM Clean up failed credentials
    del "%CREDENTIALS_FILE%" >nul 2>&1
    pause
    exit /b 1
)

REM Clean up token from memory
set GITHUB_TOKEN=
set REPO_URL=
set CREDENTIALS_FILE=

pause

