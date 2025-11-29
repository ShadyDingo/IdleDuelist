@echo off
setlocal enabledelayedexpansion

echo ========================================
echo IdleDuelist Deployment Script
echo ========================================
echo.

REM Check if git is available
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed or not in PATH!
    echo.
    echo Please install Git from: https://git-scm.com/download/win
    echo Or run these commands in Git Bash:
    echo   git add fly.toml Dockerfile server.py .github\workflows\deploy.yml
    echo   git commit -m "Update deployment assets"
    echo   git push
    echo.
    pause
    exit /b 1
)

echo [OK] Git found
echo.

REM Check if we're in a git repository
if not exist .git (
    echo [ERROR] Not a git repository!
    echo Please run this script from the project root directory.
    echo.
    pause
    exit /b 1
)

echo [OK] Git repository detected
echo.

REM Check git status
echo Checking git status...
git status --short
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to check git status
    pause
    exit /b 1
)

echo.
echo Adding changed files...
git add fly.toml Dockerfile server.py deploy.bat deploy.ps1 PUSH_TO_GITHUB.md .github/workflows/deploy.yml 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some files may not exist, continuing...
)

REM Check if there are any changes to commit
git diff --cached --quiet
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [INFO] No changes to commit. All files are up to date.
    echo.
    echo Checking if we need to push...
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
    git commit -m "Update deployment automation for Fly.io

- Add Dockerfile and fly.toml for Fly builds
- Refresh GitHub Actions workflow for Fly deploys
- Improve helper scripts and documentation"
    
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
    echo.
    echo [ERROR] Failed to push to GitHub!
    echo.
    echo Possible issues:
    echo - No remote repository configured
    echo - Authentication required
    echo - Network connection issue
    echo.
    echo If this is your first time, run: scripts\setup_git_auth.bat
    echo Or try running: git push manually
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Changes pushed successfully!
echo ========================================
echo.
echo [INFO] GitHub Actions will deploy this branch to Fly.io
echo.
echo Monitor your deployment at: https://fly.io/dashboard
echo.
pause

