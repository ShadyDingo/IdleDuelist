# Auto-Deploy to GitHub Guide

## Quick Deploy Options

### Option 1: Batch Script (Windows - Easiest)
Double-click `deploy.bat` or run from Command Prompt:
```cmd
deploy.bat
```

### Option 2: PowerShell Script
Run from PowerShell:
```powershell
.\deploy.ps1
```

### Option 3: Manual Commands
```bash
git add fly.toml Dockerfile server.py deploy.bat deploy.ps1 .github/workflows/deploy.yml
git commit -m "Update deployment automation for Fly.io"
git push
```

## What Was Fixed

### Improved `deploy.bat`:
- ✅ Checks if Git is installed
- ✅ Verifies git repository
- ✅ Auto-detects changed files
- ✅ Handles errors gracefully
- ✅ Checks if there are changes before committing
- ✅ Better error messages

### Improved `deploy.ps1`:
- ✅ Same improvements as batch file
- ✅ Better PowerShell error handling
- ✅ Checks for staged changes
- ✅ Verifies if push is needed

### Added GitHub Actions Workflow:
- ✅ Automatic deployment on push to main/master
- ✅ Runs tests before deployment
- ✅ Uses Flyctl to deploy the Docker image
- ✅ Requires `FLY_API_TOKEN` (and optional `FLY_APP_NAME`) in GitHub Secrets

## Setup GitHub Actions (Optional)

If you want automatic deployment via GitHub Actions:

1. Create a Fly API token:
   - Install Fly CLI: `fly auth login`
   - Run `fly auth token` and copy the value

2. Add to GitHub Secrets:
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Add `FLY_API_TOKEN` with the token you generated
   - (Optional) Add `FLY_APP_NAME` if you want to override the name in `fly.toml`

3. Push the workflow (already included, but re-run if you modify it):
   ```bash
   git add .github/workflows/deploy.yml
   git commit -m "Enable Fly.io deployment workflow"
   git push
   ```

## Troubleshooting

### "Git is not installed"
- Install Git: https://git-scm.com/download/win
- Or use Git Bash

### "Not a git repository"
- Make sure you're in the project root directory
- Run: `cd C:\Users\ShadyDingo\IdleDuelist\IdleDuelist`

### "Failed to push"
- Check your git credentials: `git config --global user.name` and `git config --global user.email`
- Verify remote: `git remote -v`
- Try: `git push origin main` or `git push origin master`

## Files Changed

- ✅ `deploy.bat` - Improved with error handling
- ✅ `deploy.ps1` - Improved with error handling  
- ✅ `.github/workflows/deploy.yml` - GitHub Actions workflow (Fly deploy)
- ✅ `Dockerfile` - Container build instructions for Fly.io
- ✅ `fly.toml` - Fly app + service configuration
- ✅ `.gitignore` - Updated to ignore unnecessary files

