# GitHub Token Setup for Auto-Push

## Quick Setup

Run the setup script to configure your GitHub token for automatic authentication:

### Windows (Batch):
```cmd
setup_git_token.bat
```

### PowerShell:
```powershell
.\setup_git_token.ps1
```

## What It Does

1. **Configures Git Credential Helper**: Sets up Git to store credentials securely
2. **Stores Your Token**: Saves your GitHub token in `%USERPROFILE%\.git-credentials`
3. **Tests Authentication**: Verifies the token works with your repository
4. **Secures the File**: Sets file permissions to protect your token

## After Setup

Once configured, you can use:
- `deploy.bat` - Automatic push to GitHub
- `deploy.ps1` - Automatic push to GitHub (PowerShell)
- Manual `git push` commands

All will automatically use your stored token for authentication.

## Security Notes

- ✅ Token is stored in your user profile (not in the repository)
- ✅ File permissions are set to protect the token
- ✅ Token is NOT committed to git (added to .gitignore)
- ⚠️ Keep your token secure and don't share it

## Troubleshooting

### "Authentication failed"
- Check if your token has expired
- Verify token has `repo` permissions in GitHub
- Regenerate token if needed: GitHub → Settings → Developer settings → Personal access tokens

### "Could not find git remote URL"
- Make sure you're in the git repository directory
- Check remote: `git remote -v`

### "Git is not installed"
- Install Git: https://git-scm.com/download/win
- Or use Git Bash

## Token Permissions Required

Your GitHub token needs these permissions:
- ✅ `repo` - Full control of private repositories
- ✅ `workflow` - Update GitHub Action workflows (if using Actions)

## Manual Configuration (Alternative)

If the script doesn't work, you can manually configure:

1. **Set credential helper:**
   ```cmd
   git config --global credential.helper store
   ```

2. **Create credentials file:**
   Create `%USERPROFILE%\.git-credentials` with:
   ```
   https://YOUR_TOKEN@github.com
   ```

3. **Test:**
   ```cmd
   git ls-remote origin
   ```

