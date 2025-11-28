@echo off
REM This script can be run from anywhere - it will find the project root automatically
REM Place this in the project root for easiest use

setlocal enabledelayedexpansion
title Git Authentication Setup
color 0A
mode con: cols=80 lines=30

echo.
echo ========================================
echo Git Authentication Setup
echo ========================================
echo.
echo This script configures Git authentication for automatic pushes.
echo It will automatically find the project root directory.
echo.
pause

REM Find the project root (directory containing .git folder)
set PROJECT_ROOT=%CD%
:find_git
if exist "%PROJECT_ROOT%\.git" goto found_git
if "%PROJECT_ROOT%"=="%PROJECT_ROOT:\..%" goto not_found
set PROJECT_ROOT=%PROJECT_ROOT%\..
goto find_git

:not_found
echo.
echo [ERROR] Could not find .git folder!
echo.
echo Current directory: %CD%
echo.
echo Please make sure you're running this from within the IdleDuelist project.
echo Expected location: C:\Users\ShadyDingo\IdleDuelist\IdleDuelist
echo.
echo You can run this script from:
echo   - The project root folder
echo   - The scripts folder
echo   - Any subfolder within the project
echo.
pause
exit /b 1

:found_git
REM Change to project root
cd /d "%PROJECT_ROOT%"
echo [OK] Found project root: %PROJECT_ROOT%
echo.

REM Check if git is available
REM When running from Git Bash, git should be in PATH
set GIT_CMD=git
echo Checking for Git installation...
git --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Found Git in PATH
    goto git_found
)

REM If not in PATH, check common Windows locations
echo [INFO] Git not in PATH, checking common locations...
if exist "C:\Program Files\Git\bin\git.exe" (
    set GIT_CMD="C:\Program Files\Git\bin\git.exe"
    echo [OK] Found Git at: C:\Program Files\Git\bin\git.exe
    goto git_found
)
if exist "C:\Program Files (x86)\Git\bin\git.exe" (
    set GIT_CMD="C:\Program Files (x86)\Git\bin\git.exe"
    echo [OK] Found Git at: C:\Program Files (x86)\Git\bin\git.exe
    goto git_found
)
if exist "%LOCALAPPDATA%\Programs\Git\bin\git.exe" (
    set GIT_CMD="%LOCALAPPDATA%\Programs\Git\bin\git.exe"
    echo [OK] Found Git at: %LOCALAPPDATA%\Programs\Git\bin\git.exe
    goto git_found
)

REM Git not found
echo.
echo [ERROR] Git is not found!
echo.
echo If running from Git Bash, Git should be available.
echo If running from CMD, please add Git to PATH or use Git Bash.
echo.
pause
exit /b 1

:git_found
REM Verify Git works
echo Testing Git...
if "%GIT_CMD:~0,1%"=="""" (
    %GIT_CMD% --version >nul 2>&1
) else (
    git --version >nul 2>&1
)
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git was found but doesn't work properly!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Checking Repository
echo ========================================
echo.

echo [OK] Git repository detected
if "%GIT_CMD:~0,1%"=="""" (
    echo [OK] Using Git: %GIT_CMD%
) else (
    echo [OK] Using Git: git (from PATH)
)
echo.

REM Check for existing credentials
set CREDENTIALS_FILE=%USERPROFILE%\.git-credentials
echo ========================================
echo Checking Existing Credentials
echo ========================================
echo.

if exist "%CREDENTIALS_FILE%" (
    echo [INFO] Found existing credentials file
    echo Checking if authentication works...
    if "%GIT_CMD:~0,1%"=="""" (
        %GIT_CMD% ls-remote --heads origin >nul 2>&1
    ) else (
        git ls-remote --heads origin >nul 2>&1
    )
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Existing credentials are working!
        echo.
        echo No setup needed. You can use deploy.bat to push changes.
        echo.
        pause
        exit /b 0
    ) else (
        echo [WARNING] Existing credentials may be invalid or expired
        echo.
    )
) else (
    echo [INFO] No existing credentials found
    echo.
)

REM Check if credential helper is configured
echo ========================================
echo Configuring Credential Helper
echo ========================================
echo.

if "%GIT_CMD:~0,1%"=="""" (
    %GIT_CMD% config --global credential.helper >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo Configuring Git credential helper...
        %GIT_CMD% config --global credential.helper store
    ) else (
        echo [OK] Credential helper already configured
        goto cred_helper_done
    )
) else (
    git config --global credential.helper >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo Configuring Git credential helper...
        git config --global credential.helper store
    ) else (
        echo [OK] Credential helper already configured
        goto cred_helper_done
    )
)
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to configure credential helper
    pause
    exit /b 1
)
echo [OK] Credential helper configured
:cred_helper_done
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to configure credential helper
        pause
        exit /b 1
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
pause

set /p GITHUB_TOKEN="Enter your GitHub Personal Access Token: "

if "!GITHUB_TOKEN!"=="" (
    echo.
    echo [ERROR] No token provided
    pause
    exit /b 1
)

REM Validate token format (GitHub tokens start with ghp_)
echo !GITHUB_TOKEN! | findstr /R "^ghp_" >nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] Token doesn't match expected format (should start with 'ghp_')
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        exit /b 1
    )
)

echo.
echo ========================================
echo Configuring Credentials
echo ========================================
echo.

REM Get repository URL
if "%GIT_CMD:~0,1%"=="""" (
    for /f "tokens=*" %%i in ('%GIT_CMD% remote get-url origin 2^>nul') do set REPO_URL=%%i
) else (
    for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul') do set REPO_URL=%%i
)
if "!REPO_URL!"=="" (
    echo [ERROR] Could not find git remote URL
    pause
    exit /b 1
)

echo [INFO] Repository: !REPO_URL!
echo Creating credentials file...

REM Create credentials file
echo https://!GITHUB_TOKEN!@github.com > "%CREDENTIALS_FILE%"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create credentials file
    pause
    exit /b 1
)

REM Set secure permissions (Windows)
icacls "%CREDENTIALS_FILE%" /inheritance:r /grant:r "%USERNAME%:R" >nul 2>&1

echo [OK] Credentials file created at: %CREDENTIALS_FILE%
echo.

REM Test the configuration
echo ========================================
echo Testing Authentication
echo ========================================
echo.

echo Testing connection to GitHub...
if "%GIT_CMD:~0,1%"=="""" (
    %GIT_CMD% ls-remote --heads origin >nul 2>&1
) else (
    git ls-remote --heads origin >nul 2>&1
)
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo [SUCCESS] Authentication successful!
    echo ========================================
    echo.
    echo Your GitHub token has been configured and tested.
    echo.
    echo You can now use deploy.bat to automatically push changes to GitHub.
    echo.
    echo Next steps:
    echo   1. Run: deploy.bat
    echo   2. It will add, commit, and push your changes
    echo   3. Railway will automatically deploy on push
    echo.
) else (
    echo.
    echo ========================================
    echo [ERROR] Authentication failed!
    echo ========================================
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
    echo [INFO] Removed invalid credentials file
    echo.
)

REM Clean up token from memory
set GITHUB_TOKEN=
set REPO_URL=
set CREDENTIALS_FILE=

echo.
echo ========================================
echo Press any key to close this window...
echo ========================================
pause >nul

