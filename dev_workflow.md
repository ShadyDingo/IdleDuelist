# Idle Duelist - Development Workflow Guide

This guide helps you set up an efficient development workflow for testing Idle Duelist during development.

## 🚀 Quick Start

### 1. Initial Setup
```bash
# Run the setup script to install all dependencies
python setup_dev_environment.py
```

### 2. Run All Tests
```bash
# Run comprehensive tests to verify everything works
python run_tests.py
```

### 3. Quick Development Testing
```bash
# For rapid feedback during development
python quick_test.py
```

## 📋 Testing Options

### Desktop Testing
```bash
# Test desktop version functionality
python test_desktop.py

# Run the actual desktop game
python game/main.py
```

### Mobile Testing
```bash
# Test mobile version functionality
python test_mobile.py

# Run the mobile app (requires Kivy)
python mobile_app.py
```

### Android Testing
```bash
# Build Android APK for testing
buildozer android debug

# Install on connected device
buildozer android deploy
```

## 🔄 Development Workflow

### Daily Development Cycle

1. **Start Development Session**
   ```bash
   python quick_test.py  # Quick verification
   ```

2. **Make Changes**
   - Edit game files
   - Add new features
   - Fix bugs

3. **Test Changes**
   ```bash
   python quick_test.py  # Quick test
   python run_tests.py  # Full test suite
   ```

4. **Test Specific Components**
   ```bash
   python test_desktop.py  # Desktop features
   python test_mobile.py   # Mobile features
   ```

5. **End Development Session**
   ```bash
   python run_tests.py  # Final verification
   ```

### Feature Development Workflow

1. **Plan Feature**
   - Define requirements
   - Design interface
   - Plan implementation

2. **Implement Core Logic**
   ```bash
   python quick_test.py  # Test core functionality
   ```

3. **Add UI Components**
   ```bash
   python test_mobile.py  # Test mobile UI
   ```

4. **Integration Testing**
   ```bash
   python run_tests.py  # Full integration test
   ```

5. **Platform Testing**
   ```bash
   python game/main.py      # Desktop testing
   python mobile_app.py     # Mobile testing
   buildozer android debug  # Android testing
   ```

## 🛠️ Development Tools

### Testing Scripts

- **`quick_test.py`**: Fastest test for core functionality
- **`test_desktop.py`**: Comprehensive desktop testing
- **`test_mobile.py`**: Mobile version testing
- **`run_tests.py`**: Complete test suite

### Setup Scripts

- **`setup_dev_environment.py`**: Install all dependencies
- **`buildozer.spec`**: Android build configuration

### Game Entry Points

- **`game/main.py`**: Desktop game launcher
- **`mobile_app.py`**: Mobile app launcher

## 🐛 Debugging Tips

### Common Issues

1. **Import Errors**
   ```bash
   # Check if all dependencies are installed
   python setup_dev_environment.py
   ```

2. **Mobile App Won't Start**
   ```bash
   # Test mobile dependencies
   python test_mobile.py
   ```

3. **Android Build Fails**
   ```bash
   # Check Android SDK/NDK installation
   buildozer android debug --verbose
   ```

### Debug Commands

```bash
# Verbose test output
python -v run_tests.py

# Check Python path
python -c "import sys; print(sys.path)"

# Test specific module
python -c "from game.core.player import Player; print('Player module OK')"
```

## 📱 Mobile Development Tips

### Testing on Different Platforms

1. **Desktop Testing** (Fastest)
   ```bash
   python mobile_app.py
   ```

2. **Android Emulator**
   ```bash
   buildozer android debug
   adb install bin/idleduelist-0.1.0-debug.apk
   ```

3. **Physical Android Device**
   ```bash
   buildozer android debug
   buildozer android deploy
   ```

### Mobile-Specific Testing

- Test touch interactions
- Verify responsive layouts
- Check performance on different screen sizes
- Test orientation changes

## 🔧 Configuration

### Environment Variables

```bash
# For Android builds
export ANDROIDSDK="/path/to/android/sdk"
export ANDROIDNDK="/path/to/android/ndk"

# For Java (if needed)
export JAVA_HOME="/path/to/java"
```

### Buildozer Configuration

Edit `buildozer.spec` for:
- App permissions
- Android API levels
- Package configuration
- Asset inclusion

## 📊 Performance Testing

### Desktop Performance
```bash
# Test with different player counts
python -c "
from test_desktop import test_desktop_game
import time
start = time.time()
test_desktop_game()
print(f'Test completed in {time.time() - start:.2f} seconds')
"
```

### Mobile Performance
```bash
# Test mobile app startup time
python -c "
import time
start = time.time()
from mobile_app import IdleDuelistApp
print(f'Mobile app import time: {time.time() - start:.2f} seconds')
"
```

## 🚀 Deployment Testing

### Pre-Deployment Checklist

1. **Run Full Test Suite**
   ```bash
   python run_tests.py
   ```

2. **Test All Platforms**
   ```bash
   python game/main.py      # Desktop
   python mobile_app.py     # Mobile
   buildozer android debug  # Android
   ```

3. **Performance Verification**
   ```bash
   python quick_test.py  # Should complete in < 5 seconds
   ```

4. **Final Build Test**
   ```bash
   buildozer android release  # Release build
   ```

## 📝 Development Notes

### File Structure
```
IdleDuelist/
├── game/              # Core game logic
├── mobile_ui/         # Mobile UI components
├── assets/            # Game assets
├── *.py              # Testing scripts
├── buildozer.spec    # Android build config
└── README.md         # Documentation
```

### Key Files for Development
- `game/core/` - Core game systems
- `mobile_ui/screens/` - Mobile UI screens
- `mobile_app.py` - Mobile app entry point
- `test_*.py` - Testing scripts

### Version Control
- Commit after each successful test run
- Tag releases after full test suite passes
- Keep testing scripts up to date with new features

## 🆘 Getting Help

### Common Commands Reference
```bash
# Setup
python setup_dev_environment.py

# Quick test
python quick_test.py

# Full test
python run_tests.py

# Desktop game
python game/main.py

# Mobile app
python mobile_app.py

# Android build
buildozer android debug
```

### Troubleshooting
1. Check `run_tests.py` output for specific errors
2. Verify all dependencies are installed
3. Check file paths and imports
4. Test individual components with specific test scripts




