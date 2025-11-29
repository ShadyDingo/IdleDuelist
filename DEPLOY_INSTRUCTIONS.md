# Deployment Instructions

## Quick Deploy

Run the `deploy.bat` file (double-click it), or run these commands in Git Bash or Command Prompt:

```bash
git add fly.toml Dockerfile server.py .github/workflows/deploy.yml
git commit -m "Update deployment automation for Fly.io"
git push
```

## What Was Fixed

1. **Login Endpoint (`/api/login`)**:
   - Fixed Request parameter conflict
   - Added comprehensive error handling
   - Improved database connection cleanup
   - Added JWT token creation error handling

2. **Register Endpoint (`/api/register`)**:
   - Fixed Request parameter conflict
   - Added comprehensive error handling
   - Added input validation (username length, password length)
   - Improved database connection cleanup

3. **Deployment Configuration**:
   - Added `Dockerfile` for reproducible Fly.io builds
   - Added/updated `fly.toml` with service + health check settings
   - Refreshed `.github/workflows/deploy.yml` to use Flyctl

4. **Production Validation**:
   - Added JWT_SECRET_KEY validation at startup

## After Deployment

GitHub Actions will build the Docker image and deploy to Fly.io. Monitor it at:
- GitHub Actions → `Deploy to Fly.io`
- Fly dashboard: https://fly.io/dashboard

The deployment should fix the 500 errors on both login and register endpoints.

