# Deployment Scripts

## Setup Scripts

### `setup_git_auth.bat` / `setup_git_auth.ps1`

**Purpose**: Configure Git authentication for automatic GitHub pushes

**When to run**: Once, when setting up the project on a new machine

**What it does**:
1. Checks if Git is installed
2. Verifies existing credentials (if any)
3. Prompts for GitHub Personal Access Token
4. Configures Git credential helper
5. Tests authentication
6. Stores credentials securely

**Usage**:
```cmd
scripts\setup_git_auth.bat
```

**Requirements**:
- Git installed
- GitHub Personal Access Token with `repo` scope
- Run from project root directory

**Security**:
- Token stored in `%USERPROFILE%\.git-credentials` (not in repository)
- File permissions restrict access
- Token never committed to git

## Notes

- Scripts are idempotent (safe to run multiple times)
- Will detect and use existing credentials if they work
- Will prompt for new token if existing one fails
- No hardcoded secrets in scripts

