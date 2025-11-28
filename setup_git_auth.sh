#!/bin/bash
# Git Authentication Setup Script for Git Bash
# This script configures Git authentication for automatic pushes

echo "========================================"
echo "Git Authentication Setup"
echo "========================================"
echo ""
echo "This script configures Git authentication for automatic pushes."
echo ""

# Find project root (directory containing .git folder)
PROJECT_ROOT="$(pwd)"
while [ ! -d "$PROJECT_ROOT/.git" ] && [ "$PROJECT_ROOT" != "/" ]; do
    PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
done

if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "[ERROR] Could not find .git folder!"
    echo ""
    echo "Please make sure you're running this from within the IdleDuelist project."
    echo "Expected location: /c/Users/ShadyDingo/IdleDuelist/IdleDuelist"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

cd "$PROJECT_ROOT"
echo "[OK] Found project root: $PROJECT_ROOT"
echo ""

# Check if Git is available
if ! command -v git &> /dev/null; then
    echo "[ERROR] Git is not found!"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[OK] Found Git: $(git --version)"
echo ""

# Check for existing credentials
CREDENTIALS_FILE="$HOME/.git-credentials"
echo "========================================"
echo "Checking Existing Credentials"
echo "========================================"
echo ""

if [ -f "$CREDENTIALS_FILE" ]; then
    echo "[INFO] Found existing credentials file"
    echo "Checking if authentication works..."
    if git ls-remote --heads origin &> /dev/null; then
        echo "[OK] Existing credentials are working!"
        echo ""
        echo "No setup needed. You can use deploy.bat to push changes."
        echo ""
        read -p "Press Enter to exit..."
        exit 0
    else
        echo "[WARNING] Existing credentials may be invalid or expired"
        echo ""
    fi
else
    echo "[INFO] No existing credentials found"
    echo ""
fi

# Check if credential helper is configured
echo "========================================"
echo "Configuring Credential Helper"
echo "========================================"
echo ""

if git config --global credential.helper &> /dev/null; then
    echo "[OK] Credential helper already configured"
else
    echo "Configuring Git credential helper..."
    git config --global credential.helper store
    if [ $? -eq 0 ]; then
        echo "[OK] Credential helper configured"
    else
        echo "[ERROR] Failed to configure credential helper"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

echo ""
echo "========================================"
echo "Token Setup Required"
echo "========================================"
echo ""
echo "You need a GitHub Personal Access Token (PAT) with 'repo' permissions."
echo ""
echo "Option 1: Use existing token"
echo "  - If you already have a token, paste it when prompted"
echo ""
echo "Option 2: Create new token"
echo "  1. Go to: https://github.com/settings/tokens"
echo "  2. Click 'Generate new token (classic)'"
echo "  3. Name it: 'IdleDuelist Auto-Push'"
echo "  4. Select scope: 'repo' (Full control of private repositories)"
echo "  5. Click 'Generate token'"
echo "  6. Copy the token (you'll only see it once!)"
echo ""
echo "========================================"
echo ""
read -p "Press Enter to continue..."

read -sp "Enter your GitHub Personal Access Token: " GITHUB_TOKEN
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo ""
    echo "[ERROR] No token provided"
    read -p "Press Enter to exit..."
    exit 1
fi

# Validate token format
if [[ ! "$GITHUB_TOKEN" =~ ^ghp_ ]]; then
    echo ""
    echo "[WARNING] Token doesn't match expected format (should start with 'ghp_')"
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        exit 1
    fi
fi

echo ""
echo "========================================"
echo "Configuring Credentials"
echo "========================================"
echo ""

# Get repository URL
REPO_URL=$(git remote get-url origin 2>/dev/null)
if [ -z "$REPO_URL" ]; then
    echo "[ERROR] Could not find git remote URL"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[INFO] Repository: $REPO_URL"
echo "Creating credentials file..."

# Create credentials file
echo "https://${GITHUB_TOKEN}@github.com" > "$CREDENTIALS_FILE"
chmod 600 "$CREDENTIALS_FILE"

echo "[OK] Credentials file created at: $CREDENTIALS_FILE"
echo ""

# Test the configuration
echo "========================================"
echo "Testing Authentication"
echo "========================================"
echo ""

echo "Testing connection to GitHub..."
if git ls-remote --heads origin &> /dev/null; then
    echo ""
    echo "========================================"
    echo "[SUCCESS] Authentication successful!"
    echo "========================================"
    echo ""
    echo "Your GitHub token has been configured and tested."
    echo ""
    echo "You can now use deploy.bat to automatically push changes to GitHub."
    echo ""
    echo "Next steps:"
    echo "  1. Run: deploy.bat"
    echo "  2. It will add, commit, and push your changes"
    echo "  3. Railway will automatically deploy on push"
    echo ""
else
    echo ""
    echo "========================================"
    echo "[ERROR] Authentication failed!"
    echo "========================================"
    echo ""
    echo "Possible issues:"
    echo "- Token may be invalid or expired"
    echo "- Token may not have 'repo' permissions"
    echo "- Network connection issue"
    echo ""
    echo "Please verify your token at: https://github.com/settings/tokens"
    echo ""
    # Clean up failed credentials
    rm -f "$CREDENTIALS_FILE"
    echo "[INFO] Removed invalid credentials file"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Clean up token from memory
unset GITHUB_TOKEN
unset REPO_URL

echo ""
read -p "Press Enter to close..."

