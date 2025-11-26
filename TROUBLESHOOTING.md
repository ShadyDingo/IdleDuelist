# Troubleshooting Guide

## Server Not Starting / localhost:8000 Not Working

### Step 1: Check if Python is Installed

**Windows:**
```bash
python --version
```

If that doesn't work, try:
```bash
py --version
python3 --version
```

**If Python is not found:**
1. Download Python from https://www.python.org/downloads/
2. During installation, **check "Add Python to PATH"**
3. Restart your terminal/command prompt after installation

### Step 2: Run Diagnostic Script

```bash
python check_setup.py
```

This will check:
- Python installation
- Required files
- Installed dependencies

### Step 3: Install Dependencies

If dependencies are missing:
```bash
pip install -r requirements.txt
```

If `pip` is not found, try:
```bash
python -m pip install -r requirements.txt
py -m pip install -r requirements.txt
```

### Step 4: Start the Server

**Option A: Use the batch file**
```bash
start_server.bat
```

**Option B: Use Python directly**
```bash
python start_server.py
```

**Option C: Run the server directly**
```bash
python full_web_server_simple.py
```

### Step 5: Check Server Output

When the server starts successfully, you should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Common Issues

#### "Python was not found"
- Python is not installed or not in PATH
- Solution: Install Python and add it to PATH, or use full path to Python

#### "ModuleNotFoundError: No module named 'fastapi'"
- Dependencies are not installed
- Solution: Run `pip install -r requirements.txt`

#### "Address already in use"
- Port 8000 is already taken by another application
- Solution: 
  - Close the other application using port 8000
  - Or change the port in `full_web_server_simple.py` (line 3244)

#### "Error loading page" in browser
- Server is not running
- Solution: Make sure the server is started and check for errors in the terminal

#### Browser shows "This site can't be reached"
- Server is not running or wrong URL
- Solution: 
  - Verify server is running (check terminal output)
  - Try: http://127.0.0.1:8000 instead of http://localhost:8000
  - Check Windows Firewall settings

### Manual Server Start

If the startup script doesn't work, you can start the server manually:

1. Open a terminal in the project directory
2. Run:
   ```bash
   python full_web_server_simple.py
   ```
3. Wait for "Uvicorn running on http://127.0.0.1:8000"
4. Open browser to http://localhost:8000

### Still Having Issues?

1. Check the terminal/command prompt for error messages
2. Make sure you're in the correct directory (IdleDuelist folder)
3. Verify all files are present (especially `static/full_game.html`)
4. Try running `python check_setup.py` to diagnose issues

