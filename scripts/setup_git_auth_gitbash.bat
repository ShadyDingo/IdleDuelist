@echo off
REM This script can be run from anywhere - it will find the project root automatically

echo ========================================
echo Git Authentication Setup
echo ========================================
echo.
echo This script configures Git authentication for automatic pushes.
echo.

REM Find the project root (directory containing .git folder)
set PROJECT_ROOT=%CD%
:find_git
if exist "%PROJECT_ROOT%\.git" goto found_git
if "%PROJECT_ROOT%"=="%PROJECT_ROOT:\..%" goto not_found
set PROJECT_ROOT=%PROJECT_ROOT%\..
goto find_git

:not_found
echo [ERROR] Could not find .git folder!
echo.
echo Please make sure you're running this from within the IdleDuelist project.
echo Expected location: C:\Users\ShadyDingo\IdleDuelist\IdleDuelist
echo.
pause
exit /b 1

:found_git
REM Change to project root
cd /d "%PROJECT_ROOT%"
echo [OK] Found project root: %PROJECT_ROOT%
echo.

echo [OK] Git repository detected
echo.

REM Check for existing credentials
set CREDENTIALS_FILE=%USERPROFILE%\.git-credentials
if exist "%CREDENTIALS_FILE%" (
    echo [INFO] Found existing credentials file
    echo Checking if authentication works...
    git ls-remote --heads origin >nul 2>&1
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
git config --global credential.helper >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Configuring Git credential helper...
    git config --global credential.helper store
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
for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul') do set REPO_URL=%%i
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
git ls-remote --heads origin >nul 2>&1
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

