@echo off
setlocal enabledelayedexpansion
title Applying GitHub Token

echo ========================================
echo Applying GitHub Token
echo ========================================
echo.

REM Your GitHub token (removed for security - stored in credentials file)
REM Token has been applied to %USERPROFILE%\.git-credentials

REM Find project root
set PROJECT_ROOT=%CD%
:find_git
if exist "%PROJECT_ROOT%\.git" goto found_git
if "%PROJECT_ROOT%"=="%PROJECT_ROOT:\..%" goto not_found
set PROJECT_ROOT=%PROJECT_ROOT%\..
goto find_git

:not_found
echo [ERROR] Could not find .git folder!
pause
exit /b 1

:found_git
cd /d "%PROJECT_ROOT%"
echo [OK] Project root: %PROJECT_ROOT%
echo.

REM Check for Git
set GIT_CMD=git
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if exist "C:\Program Files\Git\bin\git.exe" (
        set GIT_CMD="C:\Program Files\Git\bin\git.exe"
    ) else (
        echo [ERROR] Git not found!
        pause
        exit /b 1
    )
)

echo [OK] Git found
echo.

REM Configure credential helper
echo Configuring Git credential helper...
%GIT_CMD% config --global credential.helper store
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to configure credential helper
    pause
    exit /b 1
)
echo [OK] Credential helper configured
echo.

REM Create credentials file
set CREDENTIALS_FILE=%USERPROFILE%\.git-credentials
echo Creating credentials file...
echo https://%GITHUB_TOKEN%@github.com > "%CREDENTIALS_FILE%"

REM Set secure permissions
icacls "%CREDENTIALS_FILE%" /inheritance:r /grant:r "%USERNAME%:R" >nul 2>&1

echo [OK] Credentials file created
echo.

REM Test authentication
echo Testing authentication...
%GIT_CMD% ls-remote --heads origin >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Authentication successful!
    echo.
    echo ========================================
    echo [SUCCESS] Token applied and verified!
    echo ========================================
    echo.
) else (
    echo [ERROR] Authentication failed!
    echo Please check your token.
    del "%CREDENTIALS_FILE%" >nul 2>&1
    pause
    exit /b 1
)

REM Clean up token from script
set GITHUB_TOKEN=

echo Now adding and pushing changes...
echo.

REM Add all changes
echo Adding changes...
%GIT_CMD% add -A
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to add files
    pause
    exit /b 1
)

REM Check if there are changes to commit
%GIT_CMD% diff --cached --quiet
if %ERRORLEVEL% EQU 0 (
    echo [INFO] No changes to commit
    echo Checking if we need to push...
    %GIT_CMD% diff --quiet origin/main HEAD 2>nul
    if %ERRORLEVEL% EQU 0 (
        %GIT_CMD% diff --quiet origin/master HEAD 2>nul
        if %ERRORLEVEL% EQU 0 (
            echo [INFO] Everything is up to date
            pause
            exit /b 0
        )
    )
) else (
    echo Committing changes...
    %GIT_CMD% commit -m "Configure GitHub authentication and update deployment scripts

- Add GitHub token configuration
- Update deployment scripts for better Git Bash compatibility
- Add bash script for Git Bash users
- Improve error handling and path detection"
    
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to commit
        pause
        exit /b 1
    )
    echo [OK] Changes committed
)

echo.
echo Pushing to GitHub...
%GIT_CMD% push
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to push
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Token applied and changes pushed!
echo ========================================
echo.
echo Railway will automatically detect the push and deploy.
echo Monitor at: https://railway.app
echo.
pause

