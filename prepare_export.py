#!/usr/bin/env python3
"""
Export preparation script for Idle Duelist
This script prepares your game for mobile export by:
1. Checking all required files exist
2. Validating the buildozer.spec configuration
3. Creating a deployment package
"""

import os
import json
import zipfile
from pathlib import Path

def check_required_files():
    """Check if all required files exist for export"""
    required_files = [
        'idle_duelist.py',
        'buildozer.spec',
        'assets/idle_duelist_icon_logo.png',
        'assets/backgrounds/main_menu_background.png',
        'assets/backgrounds/loadout_menu_background.png',
        'assets/backgrounds/duel_background.png',
        'assets/backgrounds/leaderboard_menu_background.png',
        'music/main_theme.wav',
        'music/duel_theme.wav'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_assets():
    """Check if all asset directories exist"""
    asset_dirs = [
        'assets/armor',
        'assets/weapons', 
        'assets/backgrounds',
        'assets/ui',
        'music'
    ]
    
    missing_dirs = []
    for dir in asset_dirs:
        if not os.path.exists(dir):
            missing_dirs.append(dir)
    
    if missing_dirs:
        print("❌ Missing asset directories:")
        for dir in missing_dirs:
            print(f"   - {dir}")
        return False
    else:
        print("✅ All asset directories present")
        return True

def validate_buildozer_spec():
    """Validate buildozer.spec configuration"""
    if not os.path.exists('buildozer.spec'):
        print("❌ buildozer.spec not found")
        return False
    
    with open('buildozer.spec', 'r') as f:
        content = f.read()
    
    required_configs = [
        'title = Idle Duelist',
        'package.name = idleduelist',
        'orientation = portrait',
        'fullscreen = 1',
        'icon.filename = assets/idle_duelist_icon_logo.png'
    ]
    
    missing_configs = []
    for config in required_configs:
        if config not in content:
            missing_configs.append(config)
    
    if missing_configs:
        print("❌ Missing buildozer.spec configurations:")
        for config in missing_configs:
            print(f"   - {config}")
        return False
    else:
        print("✅ buildozer.spec configuration valid")
        return True

def create_export_package():
    """Create a zip package for export"""
    print("📦 Creating export package...")
    
    # Files to include in export
    include_files = [
        'idle_duelist.py',
        'buildozer.spec',
        'requirements.txt',
        'player_data.json',
        'MOBILE_EXPORT_GUIDE.md'
    ]
    
    # Directories to include
    include_dirs = [
        'assets',
        'music'
    ]
    
    zip_filename = 'IdleDuelist_Export.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add individual files
        for file in include_files:
            if os.path.exists(file):
                zipf.write(file)
                print(f"   Added: {file}")
        
        # Add directories
        for dir in include_dirs:
            if os.path.exists(dir):
                for root, dirs, files in os.walk(dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, '.')
                        zipf.write(file_path, arcname)
                        print(f"   Added: {arcname}")
    
    print(f"✅ Export package created: {zip_filename}")
    return zip_filename

def main():
    print("🎮 Idle Duelist - Export Preparation")
    print("=" * 40)
    
    # Check all requirements
    files_ok = check_required_files()
    assets_ok = check_assets()
    spec_ok = validate_buildozer_spec()
    
    if files_ok and assets_ok and spec_ok:
        print("\n✅ All checks passed! Your game is ready for export.")
        
        # Create export package
        export_file = create_export_package()
        
        print(f"\n📱 Next Steps:")
        print(f"1. Upload {export_file} to Google Drive")
        print(f"2. Use Google Colab with the provided script")
        print(f"3. Or follow the MOBILE_EXPORT_GUIDE.md")
        print(f"4. Build your APK and enjoy on mobile!")
        
    else:
        print("\n❌ Some issues found. Please fix them before exporting.")
        return False
    
    return True

if __name__ == "__main__":
    main()





