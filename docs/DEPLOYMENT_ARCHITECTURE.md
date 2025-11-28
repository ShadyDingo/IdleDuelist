# Deployment Architecture

## Overview

This document explains the deployment architecture for IdleDuelist, focusing on stability, maintainability, and avoiding fragile foundations.

## Core Principles

1. **Check Before Configure**: Always verify existing configuration before making changes
2. **Fail Gracefully**: Provide clear error messages and recovery steps
3. **No Hardcoded Secrets**: Never commit tokens or credentials to the repository
4. **Idempotent Operations**: Scripts can be run multiple times safely
5. **Clear Separation**: Deployment scripts are separate from application code

## Architecture Components

### 1. Git Authentication (`scripts/setup_git_auth.*`)

**Purpose**: Configure Git to authenticate with GitHub using a Personal Access Token (PAT)

**How it works**:
- Checks for existing credentials first
- Only sets up if needed or if existing credentials fail
- Stores credentials in `%USERPROFILE%\.git-credentials` (user-specific, not in repo)
- Uses Git's built-in credential helper (standard approach)
- Tests authentication before completing setup

**Why this approach**:
- ✅ Uses Git's standard credential storage (not custom solution)
- ✅ Works with existing Git configurations
- ✅ Credentials stored outside repository (secure)
- ✅ Can be updated without changing code
- ✅ Works across different machines/users

**Security**:
- Token stored in user profile (not in repository)
- File permissions restrict access to current user
- Token never committed to git (in .gitignore)
- Can be updated/rotated without code changes

### 2. Deployment Scripts (`deploy.bat`, `deploy.ps1`)

**Purpose**: Automate the git workflow (add, commit, push)

**How it works**:
- Checks Git availability
- Verifies repository state
- Detects changed files
- Commits with descriptive messages
- Pushes to GitHub (triggers Railway auto-deploy)

**Why this approach**:
- ✅ Simple, focused scripts (single responsibility)
- ✅ Clear error messages
- ✅ Handles edge cases (no changes, auth failures, etc.)
- ✅ Can be run manually or automated
- ✅ Doesn't depend on external services

### 3. Railway Integration

**Purpose**: Automatic deployment when code is pushed to GitHub

**How it works**:
- Railway watches GitHub repository
- On push to main/master, triggers build
- Uses `railway.json` and `nixpacks.toml` for configuration
- Builds and deploys automatically

**Why this approach**:
- ✅ Standard CI/CD pattern (GitHub → Railway)
- ✅ No custom deployment scripts needed
- ✅ Railway handles infrastructure
- ✅ Can be monitored via Railway dashboard
- ✅ Rollback available if needed

## File Structure

```
IdleDuelist/
├── scripts/
│   ├── setup_git_auth.bat      # Windows setup script
│   └── setup_git_auth.ps1      # PowerShell setup script
├── deploy.bat                   # Windows deployment script
├── deploy.ps1                   # PowerShell deployment script
├── railway.json                 # Railway deployment config
├── nixpacks.toml                # Nixpacks build config
├── .gitignore                   # Excludes credentials/tokens
└── docs/
    └── DEPLOYMENT_ARCHITECTURE.md  # This file
```

## Workflow

### Initial Setup (One-Time)

1. Run `scripts/setup_git_auth.bat`
2. Enter GitHub Personal Access Token when prompted
3. Script verifies authentication works
4. Done! Credentials stored securely

### Daily Development

1. Make code changes
2. Run `deploy.bat`
3. Script handles: add → commit → push
4. Railway automatically detects push and deploys

## Why This Architecture is Solid

### 1. **Uses Standard Tools**
- Git's built-in credential helper (not custom solution)
- Standard Git workflow (add, commit, push)
- Railway's standard GitHub integration

### 2. **Separation of Concerns**
- Authentication setup: separate script
- Deployment: separate script
- Application code: no deployment logic

### 3. **No Fragile Dependencies**
- Doesn't depend on specific Git versions
- Doesn't require specific tools installed
- Works with standard Git configurations
- Can work without scripts (manual git commands)

### 4. **Easy to Maintain**
- Clear file structure
- Well-documented
- Can update token without code changes
- Scripts are simple and readable

### 5. **Secure by Default**
- No secrets in code
- Credentials stored securely
- Token can be rotated easily
- File permissions protect credentials

## Common Questions

### Q: Why not use SSH keys instead of tokens?

**A**: Both work, but tokens are:
- Easier to set up (no key generation)
- Easier to revoke (just delete token)
- Work with HTTPS (simpler for Windows)
- Can have specific scopes (more secure)

### Q: Why not use GitHub Actions for deployment?

**A**: We could, but:
- Railway's GitHub integration is simpler
- No need for additional CI/CD setup
- Railway handles the deployment directly
- Less moving parts = more stable

### Q: What if the token expires?

**A**: Just run `setup_git_auth.bat` again with a new token. The script will:
- Detect the old token doesn't work
- Prompt for a new one
- Update credentials automatically

### Q: Can I use this on multiple machines?

**A**: Yes! Each machine needs:
1. Git installed
2. Run `setup_git_auth.bat` once
3. Use the same token (or create machine-specific tokens)

## Future Improvements

Potential enhancements (not needed now, but possible):

1. **Environment Variables**: Store token in environment variable instead of file
2. **Token Rotation**: Script to automatically rotate tokens
3. **Multi-Environment**: Support staging/production branches
4. **Deployment Notifications**: Slack/Discord notifications on deploy
5. **Pre-deploy Checks**: Run tests before deploying

These are optional and can be added without breaking existing setup.

## Troubleshooting

See `docs/TROUBLESHOOTING.md` for common issues and solutions.

## Summary

This architecture is designed to be:
- ✅ **Stable**: Uses standard tools and patterns
- ✅ **Maintainable**: Clear structure and documentation
- ✅ **Secure**: No secrets in code, proper credential storage
- ✅ **Flexible**: Can be extended without breaking changes
- ✅ **Simple**: Easy to understand and use

The foundation is solid and won't break with future changes or updates.

