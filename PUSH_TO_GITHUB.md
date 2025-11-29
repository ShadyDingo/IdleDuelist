# Push Changes to GitHub

## Quick Commands

Open **Git Bash**, **Command Prompt**, or **PowerShell** and run these commands:

```bash
# Navigate to the project directory (if not already there)
cd C:\Users\ShadyDingo\IdleDuelist\IdleDuelist

# Check what files have changed
git status

# Add the modified files
git add fly.toml Dockerfile server.py .github/workflows/deploy.yml

# Commit with a descriptive message
git commit -m "Update deployment automation for Fly.io"

# Push to GitHub (GitHub Actions will deploy to Fly.io)
git push
```

## Files Changed

1. **`Dockerfile`** - Reproducible container build for Fly.io
2. **`fly.toml`** - Fly.io service definition (ports, checks, concurrency)
3. **`.github/workflows/deploy.yml`** - GitHub Actions workflow that runs Flyctl
4. **`server.py`** - Backend fixes (login/register hardening and health logging)

## After Pushing

GitHub Actions will run tests and deploy to Fly.io automatically. Monitor it at:
- **GitHub Actions** → `Deploy to Fly.io`
- **Fly Dashboard**: https://fly.io/dashboard

The deployment should fix the 500 errors on both `/api/login` and `/api/register` endpoints.

