# Deployment Instructions

## Quick Deploy

Run the `deploy.bat` file (double-click it), or run these commands in Git Bash or Command Prompt:

```bash
git add nixpacks.toml railway.json server.py
git commit -m "Fix login and register endpoints: add error handling and fix Request parameter issues

- Add nixpacks.toml for explicit dependency installation
- Update railway.json build command to use python -m pip
- Fix /api/login endpoint with proper error handling and Request parameter
- Fix /api/register endpoint with proper error handling and Request parameter
- Add JWT_SECRET_KEY validation for production
- Improve database connection cleanup in both endpoints"
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
   - Added `nixpacks.toml` for explicit dependency installation
   - Updated `railway.json` build command

4. **Production Validation**:
   - Added JWT_SECRET_KEY validation at startup

## After Deployment

Railway will automatically detect the push and start a new deployment. Monitor it at:
- Railway Dashboard: https://railway.app

The deployment should fix the 500 errors on both login and register endpoints.

