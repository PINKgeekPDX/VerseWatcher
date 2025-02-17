# VerseWatcher

A real-time game log monitoring application that tracks and notifies you of in-game events with a modern, dark-themed interface.

## Features

- 🎮 Real-time Game.log monitoring
- 🎯 Detailed kill/death event tracking
- 🔔 Customizable toast notifications
- 🌙 Modern dark theme with gradient accents
- 👥 Party/team member tracking
- 📊 Session history with detailed event information
- 💾 Persistent settings and window geometry
- 🔧 Customizable event filters
- 📝 Detailed logging system
- 🖥️ Console output window

## Requirements

- Windows 10/11
- Python 3.8 or higher
- 100MB free disk space
- Administrator privileges (for installation)

## Installation

### Option 1: Running from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/VerseWatcher.git
   cd VerseWatcher
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: Using Pre-built Binary

1. Download the latest release from the [Releases](https://github.com/yourusername/VerseWatcher/releases) page
2. Extract the ZIP file to your desired location
3. Run `VerseWatcher.exe`

## Building from Source

To create a standalone executable:

1. Ensure you have all dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Run PyInstaller:
   ```bash
   pyinstaller verse_watcher.spec
   ```

3. The executable will be created in the `dist` directory

## Usage

1. Start the application:
   - If running from source: `python src/main.py`
   - If using executable: Run `VerseWatcher.exe`

2. Configure settings:
   - Set the game directory (containing Game.log)
   - Enter your in-game player name (case sensitive)
   - Customize toast notifications (position, size, duration)
   - Set event filters

3. Party/Team Management:
   - Add party members to track their events
   - Events involving party members appear in a separate list

4. Session History:
   - View past sessions and their events
   - Detailed information for each event
   - Filter events by type

## File Structure

```
VerseWatcher/
├── src/                    # Source code
│   ├── main.py            # Main application
│   ├── game_watcher.py    # Game log monitoring
│   ├── toast_manager.py   # Toast notifications
│   └── logger.py          # Logging system
├── venv/                   # Virtual environment
├── requirements.txt        # Python dependencies
├── verse_watcher.spec     # PyInstaller spec
├── start.bat              # Startup script
├── vw.ico                 # Application icon
└── README.md              # Documentation
```

## Data Storage

- Settings: `%USERPROFILE%\Documents\PINK\VerseWatcher\settings.json`
- Logs: `%USERPROFILE%\Documents\PINK\VerseWatcher\logs\`
- History: `%USERPROFILE%\Documents\PINK\VerseWatcher\history\`

## Troubleshooting

1. **Window not appearing:**
   - Check if another instance is running
   - Run as administrator

2. **Game.log not found:**
   - Verify the game directory path
   - Ensure Game.log exists and is readable

3. **Missing notifications:**
   - Check event filter settings
   - Verify player name is correct (case sensitive)
   - Ensure Windows notifications are enabled

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyQt5 for the GUI framework
- Watchdog for file monitoring
- The Star Citizen community
