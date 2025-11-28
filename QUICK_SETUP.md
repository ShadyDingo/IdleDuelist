# Quick Setup Guide

## How to Run the Setup Script

### Option 1: Double-Click (Easiest)
1. Open Windows Explorer
2. Navigate to your project folder: `C:\Users\ShadyDingo\IdleDuelist\IdleDuelist`
3. Go into the `scripts` folder
4. Double-click `setup_git_auth.bat`
5. Follow the prompts

### Option 2: Command Prompt
1. Open Command Prompt (CMD)
2. Navigate to your project:
   ```cmd
   cd C:\Users\ShadyDingo\IdleDuelist\IdleDuelist
   ```
3. Run the script:
   ```cmd
   scripts\setup_git_auth.bat
   ```
4. Follow the prompts

### Option 3: PowerShell
1. Open PowerShell
2. Navigate to your project:
   ```powershell
   cd C:\Users\ShadyDingo\IdleDuelist\IdleDuelist
   ```
3. Run the script:
   ```powershell
   .\scripts\setup_git_auth.ps1
   ```
4. Follow the prompts

## What Happens

1. Script checks if Git is installed
2. Checks for existing credentials
3. If needed, prompts you to paste your GitHub token
4. Tests the token to make sure it works
5. Stores it securely for future use

## After Setup

Once configured, you can use:
```cmd
deploy.bat
```

This will automatically push your changes to GitHub!

