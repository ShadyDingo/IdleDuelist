# Music Directory for Idle Duelist

## 🎵 **Adding Music to Your Game**

This directory is where you should place your MP3 music files for the Idle Duelist game.

### 📁 **Supported File Formats**
- **MP3** (.mp3) - Recommended for best compatibility
- **WAV** (.wav) - High quality, larger file size
- **OGG** (.ogg) - Good compression, open source
- **M4A** (.m4a) - Apple format

### 🎮 **How to Add Music**

1. **Place your MP3 file** in this `music/` directory
2. **Rename it** to something descriptive (e.g., `background_music.mp3`)
3. **Restart the game** - the music will be automatically detected and loaded

### 🎯 **Recommended Music Names**

For automatic background music, name your files:
- `background.mp3` - Main background music
- `main_theme.mp3` - Main menu theme
- `menu.mp3` - Menu music
- `theme.mp3` - General theme music

### 🎵 **Music Features**

The game will automatically:
- ✅ **Load all music files** from this directory
- ✅ **Play background music** on startup
- ✅ **Loop background music** continuously
- ✅ **Respect volume settings** from the settings menu
- ✅ **Pause/resume** when music is toggled off/on

### ⚙️ **Settings Integration**

Music can be controlled from the **Settings** screen:
- **Background Music** toggle - Enable/disable background music
- **Sound Effects** toggle - Enable/disable sound effects
- **Master Volume** slider - Control music volume (0-100%)

### 📱 **Mobile Compatibility**

Music files are optimized for mobile devices:
- **File size**: Keep under 10MB for best performance
- **Duration**: 2-5 minutes recommended for looping
- **Quality**: 128-192 kbps MP3 is ideal

### 🔧 **Technical Details**

The music system uses Kivy's SoundLoader:
- Automatically detects supported audio formats
- Handles loading errors gracefully
- Provides volume control and looping
- Works on both desktop and mobile platforms

### 📝 **Example Usage**

1. **Add your MP3**: `music/background_music.mp3`
2. **Start the game**: Music plays automatically
3. **Adjust settings**: Use Settings → Audio Settings
4. **Control volume**: Use the Master Volume slider

### 🎉 **Ready to Rock!**

Just drop your MP3 files in this directory and the game will handle the rest!

**Happy gaming with your custom soundtrack!** 🎵🎮







