# Push Changes to GitHub

## Quick Commands

Open **Git Bash**, **Command Prompt**, or **PowerShell** and run these commands:

```bash
# Navigate to the project directory (if not already there)
cd C:\Users\ShadyDingo\IdleDuelist\IdleDuelist

# Check what files have changed
git status

# Add the modified files
git add nixpacks.toml railway.json server.py

# Commit with a descriptive message
git commit -m "Fix login and register endpoints: improve error handling and Request parameter

- Add nixpacks.toml for explicit dependency installation
- Update railway.json build command to use python -m pip
- Fix /api/login endpoint with proper error handling and Request parameter
- Fix /api/register endpoint with proper error handling and Request parameter
- Add JWT_SECRET_KEY validation for production
- Improve database connection cleanup in both endpoints"

# Push to GitHub (Railway will auto-deploy)
git push
```

## Files Changed

1. **`nixpacks.toml`** (NEW) - Nixpacks configuration for Railway
2. **`railway.json`** (MODIFIED) - Updated build command
3. **`server.py`** (MODIFIED) - Fixed login and register endpoints

## After Pushing

Railway will automatically detect the push and start a new deployment. Monitor it at:
- **Railway Dashboard**: https://railway.app

The deployment should fix the 500 errors on both `/api/login` and `/api/register` endpoints.

