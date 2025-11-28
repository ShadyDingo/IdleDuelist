@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Apply GitHub Token and Deploy
echo ========================================
echo.
echo This script will:
echo 1. Configure your GitHub token
echo 2. Add all changes
echo 3. Commit changes
echo 4. Push to GitHub
echo.

REM Check if git is available
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed or not in PATH!
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Check if we're in a git repository
if not exist .git (
    echo [ERROR] Not a git repository!
    pause
    exit /b 1
)

REM Get token from user
echo.
set /p GITHUB_TOKEN="Enter your GitHub Personal Access Token: "

if "!GITHUB_TOKEN!"=="" (
    echo [ERROR] No token provided
    pause
    exit /b 1
)

echo.
echo Configuring Git authentication...

REM Configure credential helper if not already set
git config --global credential.helper store >nul 2>&1

REM Create credentials file
set CREDENTIALS_FILE=%USERPROFILE%\.git-credentials
echo https://!GITHUB_TOKEN!@github.com > "%CREDENTIALS_FILE%"

REM Set secure permissions
icacls "%CREDENTIALS_FILE%" /inheritance:r /grant:r "%USERNAME%:R" >nul 2>&1

echo [OK] Token configured
echo.

REM Test authentication
echo Testing authentication...
git ls-remote --heads origin >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Authentication failed! Please check your token.
    pause
    exit /b 1
)

echo [OK] Authentication successful!
echo.

REM Now deploy
echo ========================================
echo Deploying Changes
echo ========================================
echo.

REM Check git status
echo Checking for changes...
git status --short
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to check git status
    pause
    exit /b 1
)

echo.
echo Adding all changes...
git add -A
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to add files
    pause
    exit /b 1
)

REM Check if there are changes to commit
git diff --cached --quiet
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [INFO] No changes to commit. Checking if we need to push...
    git diff --quiet origin/main HEAD 2>nul
    if %ERRORLEVEL% EQU 0 (
        git diff --quiet origin/master HEAD 2>nul
        if %ERRORLEVEL% EQU 0 (
            echo [INFO] Everything is up to date. Nothing to push.
            pause
            exit /b 0
        )
    )
) else (
    echo.
    echo Committing changes...
    git commit -m "Update project: apply GitHub token and deploy configuration

- Configure GitHub authentication
- Update deployment scripts and documentation
- Improve deployment architecture"
    
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to commit changes
        pause
        exit /b 1
    )
    
    echo [OK] Changes committed
)

echo.
echo Pushing to GitHub...
git push
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to push to GitHub!
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Token configured and changes pushed!
echo ========================================
echo.
echo Railway will automatically detect the push and start a new deployment.
echo Monitor at: https://railway.app
echo.

REM Clean up token from memory
set GITHUB_TOKEN=
set CREDENTIALS_FILE=

pause

