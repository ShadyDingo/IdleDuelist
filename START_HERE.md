# 🎮 How to Start IdleDuelist

## The Problem
If `localhost:8000` isn't working, **the server isn't running yet**. You need to start it first!

## Quick Start (3 Steps)

### Step 1: Check Python
Open a terminal/command prompt and type:
```bash
python --version
```

If you see an error, Python isn't installed. Download from: https://www.python.org/downloads/
**Important:** Check "Add Python to PATH" during installation!

### Step 2: Install Dependencies

**If you get a Rust/Cargo error (bcrypt installation fails):**

**Option A - Use the special installer (Recommended):**
```bash
install_dependencies.bat
```

**Option B - Manual installation:**
```bash
python -m pip install --upgrade pip
python -m pip install --prefer-binary bcrypt
python -m pip install --prefer-binary -r requirements.txt
```

**Normal installation (if no errors):**
```bash
pip install -r requirements.txt
```

See `BCRYPT_FIX.md` for more details if you encounter Rust/Cargo errors.

### Step 3: Start the Server

**Option A - Double-click:**
- Double-click `start_server.bat`

**Option B - Command line:**
```bash
python start_server.py
```

**Option C - Direct:**
```bash
python full_web_server_simple.py
```

### Step 4: Open Browser
Once you see "Uvicorn running on http://127.0.0.1:8000", open:
- **http://localhost:8000** or
- **http://127.0.0.1:8000**

## What You Should See

When the server starts successfully:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**Keep this terminal window open!** Closing it stops the server.

## Still Not Working?

Run the diagnostic:
```bash
python check_setup.py
```

This will tell you exactly what's missing.

## Common Issues

1. **"Python not found"** → Install Python and add to PATH
2. **"Module not found"** → Run `pip install -r requirements.txt`
3. **"Port already in use"** → Another program is using port 8000
4. **Browser shows error** → Make sure server is running (check terminal)

See `TROUBLESHOOTING.md` for more help!

