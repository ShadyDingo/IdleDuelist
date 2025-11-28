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
git add nixpacks.toml railway.json server.py deploy.bat deploy.ps1
git commit -m "Fix login and register endpoints"
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
- ✅ Requires Railway token in GitHub Secrets

## Setup GitHub Actions (Optional)

If you want automatic deployment via GitHub Actions:

1. Get your Railway token:
   - Go to Railway → Settings → Tokens
   - Create a new token

2. Add to GitHub Secrets:
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Add `RAILWAY_TOKEN` with your Railway token
   - Add `RAILWAY_SERVICE_ID` with your service ID

3. Push the workflow file:
   ```bash
   git add .github/workflows/deploy.yml
   git commit -m "Add GitHub Actions deployment"
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
- ✅ `.github/workflows/deploy.yml` - GitHub Actions workflow (NEW)
- ✅ `.gitignore` - Updated to ignore unnecessary files

