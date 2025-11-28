# Git Authentication Setup
# This script configures Git authentication for automatic pushes
# It checks for existing credentials and only sets up if needed

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Git Authentication Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script configures Git authentication for automatic pushes." -ForegroundColor Gray
Write-Host "It will check for existing credentials and only set up if needed." -ForegroundColor Gray
Write-Host ""

# Check if git is available
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "[ERROR] Git is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check if we're in a git repository
if (-not (Test-Path .git)) {
    Write-Host "[ERROR] Not a git repository!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Git repository detected" -ForegroundColor Green
Write-Host ""

# Check for existing credentials
$credentialsFile = Join-Path $env:USERPROFILE ".git-credentials"
if (Test-Path $credentialsFile) {
    Write-Host "[INFO] Found existing credentials file" -ForegroundColor Cyan
    Write-Host "Checking if authentication works..." -ForegroundColor Yellow
    git ls-remote --heads origin 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Existing credentials are working!" -ForegroundColor Green
        Write-Host "No setup needed." -ForegroundColor Green
        Write-Host ""
        exit 0
    } else {
        Write-Host "[WARNING] Existing credentials may be invalid or expired" -ForegroundColor Yellow
        Write-Host ""
    }
}

# Check if credential helper is configured
$credentialHelper = git config --global credential.helper 2>&1
if ($LASTEXITCODE -ne 0 -or $credentialHelper -eq "") {
    Write-Host "Configuring Git credential helper..." -ForegroundColor Yellow
    git config --global credential.helper store
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to configure credential helper" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Credential helper configured" -ForegroundColor Green
} else {
    Write-Host "[OK] Credential helper already configured" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Token Setup Required" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You need a GitHub Personal Access Token (PAT) with 'repo' permissions." -ForegroundColor White
Write-Host ""
Write-Host "Option 1: Use existing token" -ForegroundColor Yellow
Write-Host "  - If you already have a token, paste it when prompted" -ForegroundColor Gray
Write-Host ""
Write-Host "Option 2: Create new token" -ForegroundColor Yellow
Write-Host "  1. Go to: https://github.com/settings/tokens" -ForegroundColor Gray
Write-Host "  2. Click 'Generate new token (classic)'" -ForegroundColor Gray
Write-Host "  3. Name it: 'IdleDuelist Auto-Push'" -ForegroundColor Gray
Write-Host "  4. Select scope: 'repo' (Full control of private repositories)" -ForegroundColor Gray
Write-Host "  5. Click 'Generate token'" -ForegroundColor Gray
Write-Host "  6. Copy the token (you'll only see it once!)" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get token from user
$githubToken = Read-Host "Enter your GitHub Personal Access Token" -AsSecureString
$githubTokenPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($githubToken)
)

if ([string]::IsNullOrWhiteSpace($githubTokenPlain)) {
    Write-Host "[ERROR] No token provided" -ForegroundColor Red
    exit 1
}

# Validate token format
if (-not $githubTokenPlain.StartsWith("ghp_")) {
    Write-Host "[WARNING] Token doesn't match expected format (should start with 'ghp_')" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

Write-Host ""
Write-Host "Configuring credentials..." -ForegroundColor Yellow

# Get repository URL
try {
    $repoUrl = git remote get-url origin 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Could not find git remote URL"
    }
} catch {
    Write-Host "[ERROR] Could not find git remote URL" -ForegroundColor Red
    exit 1
}

# Create credentials file
$credentials = "https://${githubTokenPlain}@github.com"
$credentials | Out-File -FilePath $credentialsFile -Encoding ASCII -NoNewline

# Set secure permissions
try {
    $acl = Get-Acl $credentialsFile
    $acl.SetAccessRuleProtection($true, $false)
    $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        $env:USERNAME,
        "Read",
        "Allow"
    )
    $acl.SetAccessRule($accessRule)
    Set-Acl -Path $credentialsFile -AclObject $acl
} catch {
    Write-Host "[WARNING] Could not set file permissions" -ForegroundColor Yellow
}

Write-Host "[OK] Credentials file created" -ForegroundColor Green
Write-Host ""

# Test the configuration
Write-Host "Testing authentication..." -ForegroundColor Yellow
git ls-remote --heads origin 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Authentication successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[SUCCESS] Git authentication configured!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now use deploy.bat to automatically push to GitHub." -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "[ERROR] Authentication failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible issues:" -ForegroundColor Yellow
    Write-Host "- Token may be invalid or expired" -ForegroundColor White
    Write-Host "- Token may not have 'repo' permissions" -ForegroundColor White
    Write-Host "- Network connection issue" -ForegroundColor White
    Write-Host ""
    Write-Host "Please verify your token at: https://github.com/settings/tokens" -ForegroundColor Yellow
    Write-Host ""
    # Clean up failed credentials
    Remove-Item $credentialsFile -ErrorAction SilentlyContinue
    exit 1
}

# Clean up token from memory
$githubTokenPlain = $null
[GC]::Collect()

