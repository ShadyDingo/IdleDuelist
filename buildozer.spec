[app]

# Application title
title = Idle Duelist

# Package name
package.name = idleduelist

# Package domain
package.domain = com.idleduelist.game

# Source code directory
source.dir = .

# Source files to include
source.include_exts = py,png,jpg,kv,atlas,PNG,wav

# Application version
version = 0.1.0

# Application requirements
requirements = python3,kivy,kivymd,pillow,plyer

# Supported orientations
orientation = portrait

# Fullscreen mode
fullscreen = 1

# Icon and presplash
icon.filename = assets/idle_duelist_icon_logo.png
presplash.filename = assets/backgrounds/main_menu_background.png

# Android specific
[android]

# Android API level
api = 33

# Minimum Android API level
minapi = 21

# Android NDK version
ndk = 25b

# Android SDK version
sdk = 33

# Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Application category
android.category = GAME

# Application theme
android.theme = android:Theme.NoTitleBar.Fullscreen

# Build configuration
[buildozer]

# Log level
log_level = 2

# Warn on root
warn_on_root = 1

