# IdleDuelist Deployment Script
# Run this script to commit and push changes to GitHub
# Railway will automatically redeploy when changes are pushed

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IdleDuelist Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is available
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "[ERROR] Git is not installed or not in PATH!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Or run these commands in Git Bash:" -ForegroundColor Yellow
    Write-Host "  git add nixpacks.toml railway.json server.py" -ForegroundColor White
    Write-Host "  git commit -m 'Fix login and register endpoints'" -ForegroundColor White
    Write-Host "  git push" -ForegroundColor White
    exit 1
}

Write-Host "[OK] Git found: $($gitCmd.Version)" -ForegroundColor Green
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path .git)) {
    Write-Host "[ERROR] Not a git repository!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Git repository detected" -ForegroundColor Green
Write-Host ""

# Check git status
Write-Host "Checking git status..." -ForegroundColor Yellow
git status --short
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to check git status" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Adding changed files..." -ForegroundColor Yellow
$filesToAdd = @("nixpacks.toml", "railway.json", "server.py", "deploy.bat", "deploy.ps1", "PUSH_TO_GITHUB.md")
$addedFiles = @()

foreach ($file in $filesToAdd) {
    if (Test-Path $file) {
        git add $file 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $addedFiles += $file
        }
    }
}

if ($addedFiles.Count -eq 0) {
    Write-Host "[WARNING] No files to add" -ForegroundColor Yellow
} else {
    Write-Host "[OK] Added $($addedFiles.Count) file(s)" -ForegroundColor Green
}

# Check if there are any changes to commit
$stagedChanges = git diff --cached --quiet 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[INFO] No changes to commit. All files are up to date." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Checking if we need to push..." -ForegroundColor Yellow
    
    # Check if local is ahead of remote
    git fetch --quiet 2>&1 | Out-Null
    $localCommits = git rev-list --count @{u}..HEAD 2>&1
    if ($LASTEXITCODE -eq 0 -and [int]$localCommits -gt 0) {
        Write-Host "[INFO] Local commits found, will push..." -ForegroundColor Cyan
    } else {
        Write-Host "[INFO] Everything is up to date. Nothing to push." -ForegroundColor Green
        exit 0
    }
} else {
    Write-Host ""
    Write-Host "Committing changes..." -ForegroundColor Yellow
    $commitMessage = @"
Fix login and register endpoints: improve error handling and Request parameter

- Add nixpacks.toml for explicit dependency installation
- Update railway.json build command to use python -m pip
- Fix /api/login endpoint with proper error handling and Request parameter
- Fix /api/register endpoint with proper error handling and Request parameter
- Add JWT_SECRET_KEY validation for production
- Improve database connection cleanup in both endpoints
- Update deployment scripts
"@
    
    git commit -m $commitMessage
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to commit changes" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[OK] Changes committed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Failed to push to GitHub!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible issues:" -ForegroundColor Yellow
    Write-Host "- No remote repository configured" -ForegroundColor White
    Write-Host "- Authentication required" -ForegroundColor White
    Write-Host "- Network connection issue" -ForegroundColor White
    Write-Host ""
    Write-Host "If this is your first time, run: .\scripts\setup_git_auth.ps1" -ForegroundColor Yellow
    Write-Host "Or try running: git push manually" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[SUCCESS] Changes pushed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Railway will automatically detect the push and start a new deployment" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitor your deployment at: https://railway.app" -ForegroundColor Yellow
Write-Host ""

