# Fixing bcrypt Installation (Rust/Cargo Error)

## The Problem
`bcrypt` requires Rust to compile from source, but on Windows you should be able to use pre-built wheels instead.

## Quick Fix

### Option 1: Use the Installation Script (Recommended)
```bash
install_dependencies.bat
```

This script installs packages in the right order using pre-built wheels.

### Option 2: Manual Installation

**Step 1: Upgrade pip**
```bash
python -m pip install --upgrade pip
```

**Step 2: Install bcrypt with pre-built wheel**
```bash
python -m pip install --prefer-binary bcrypt
```

**Step 3: Install remaining packages**
```bash
python -m pip install --prefer-binary -r requirements.txt
```

### Option 3: Install Rust (If you want to build from source)

If you prefer to build from source:
1. Install Rust from: https://rustup.rs/
2. Restart your terminal
3. Run: `pip install -r requirements.txt`

## Why This Happens

- `bcrypt` is a Python package that has C/Rust extensions
- On Windows, pre-built "wheels" (binary packages) are available
- If pip can't find a wheel, it tries to build from source (needs Rust)
- Using `--prefer-binary` forces pip to use pre-built wheels when available

## Verify Installation

After installation, test it:
```bash
python -c "import bcrypt; print('bcrypt installed successfully!')"
```

If you see "bcrypt installed successfully!", you're good to go!

## Still Having Issues?

1. Make sure you're using a recent version of pip:
   ```bash
   python -m pip install --upgrade pip
   ```

2. Try installing bcrypt from a specific source:
   ```bash
   python -m pip install bcrypt --only-binary :all:
   ```

3. Check your Python version (should be 3.7+):
   ```bash
   python --version
   ```


