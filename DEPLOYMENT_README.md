# Deployment Guide

## Quick Start

### First Time Setup

1. **Configure Git Authentication** (one-time):
   ```cmd
   scripts\setup_git_auth.bat
   ```
   - Enter your GitHub Personal Access Token when prompted
   - Script will verify it works and store it securely

2. **Deploy Changes**:
   ```cmd
   deploy.bat
   ```
   - Automatically adds, commits, and pushes changes
   - Railway will auto-deploy on push

## Architecture

This deployment system is designed to be:
- **Stable**: Uses standard Git tools and patterns
- **Secure**: No secrets in code, proper credential storage
- **Maintainable**: Clear structure, well-documented
- **Flexible**: Easy to extend without breaking changes

See `docs/DEPLOYMENT_ARCHITECTURE.md` for detailed architecture documentation.

## Why This Approach?

### You Don't Need a New Token If You Have One

The setup script:
- ✅ **Checks existing credentials first** - Won't ask for a new token if you already have one that works
- ✅ **Only prompts if needed** - If existing credentials fail, it will prompt for a new one
- ✅ **Works with any token** - Use an existing token or create a new one

### Solid Foundation

The architecture:
- ✅ Uses **standard Git tools** (credential helper) - not a custom solution
- ✅ **No hardcoded secrets** - tokens stored securely outside the repo
- ✅ **Idempotent operations** - scripts can be run multiple times safely
- ✅ **Clear separation** - setup vs deployment scripts
- ✅ **Easy to maintain** - simple scripts, well-documented

### Won't Break With Updates

- ✅ Uses Git's built-in features (standard, stable)
- ✅ No dependencies on specific versions
- ✅ Can work without scripts (manual git commands still work)
- ✅ Easy to update/rotate tokens without code changes

## Files

- `scripts/setup_git_auth.bat` - One-time authentication setup
- `deploy.bat` - Daily deployment script
- `railway.json` - Railway deployment configuration
- `nixpacks.toml` - Build configuration
- `docs/DEPLOYMENT_ARCHITECTURE.md` - Detailed architecture docs

## Troubleshooting

**"Authentication failed"**
→ Run `scripts\setup_git_auth.bat` again (token may have expired)

**"Git not found"**
→ Install Git: https://git-scm.com/download/win

**"No changes to commit"**
→ Everything is up to date, nothing to push

For more help, see the architecture documentation.

