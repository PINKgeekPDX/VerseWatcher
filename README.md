# VerseWatcher - Star Citizen Event Notifier

A real-time game.log monitoring tool ive made for Star Citizen. It tracks and notifies you of in-game events of simple but highly useful events and its details. 

This is a very early WIP of this tool. This is basically using tech ive been developing for a bigger project still in development and iv'e decided to make a more simple tool that does some of the useful stuff of the bigger project, so this is what it has become. I do plan to add more features to this tool in the future over time and keep it up to date with the latest changes in the game.

## Screenshots

![Screenshot 1](https://raw.githubusercontent.com/PINKgeekPDX/VerseWatcher/main/1.png)
![Screenshot 2](https://raw.githubusercontent.com/PINKgeekPDX/VerseWatcher/main/2.png)
![Screenshot 3](https://raw.githubusercontent.com/PINKgeekPDX/VerseWatcher/main/3.png)
![Screenshot 4](https://raw.githubusercontent.com/PINKgeekPDX/VerseWatcher/main/4.png)
![Screenshot 5](https://raw.githubusercontent.com/PINKgeekPDX/VerseWatcher/main/5.png)

## Features

- 🎮 Real-time Game.log monitoring

- 🎯 Detailed kill/death event tracking

- 🔔 Toast notifications

- 🌙 Clean UI

- 👥 Party member tracking

- 📊 App session persistent historical timeline records of events kept

## Requirements

- This app
- Star Citizen
- Python 3.8 or higher ( if you arent running from the .exe )
- 100MB free disk space

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

## Data Storage

- Settings: `%USERPROFILE%\Documents\PINK\VerseWatcher\settings.json`
- Logs: `%USERPROFILE%\Documents\PINK\VerseWatcher\logs\`
- History: `%USERPROFILE%\Documents\PINK\VerseWatcher\history\`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

- This project is licensed under the MIT License - see the LICENSE file for details.
- This app does not interfere with your game in any way. 
- It will not be flagged by anticheat as it is totally passive.