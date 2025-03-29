# [ Verse Watcher ]
# - Star Citizen Event Tool -
http://www.versewatcher.com/

**A real-time game.log monitoring tool I've made for Star Citizen.** 

*This is a very early WIP of this tool. This is basically using tech I've been developing for a bigger project still in development and I've decided to make a simpler tool that does some of the useful stuff of the bigger project, so this is what it has become.*
 
 *I do plan to add more features to this tool in the future over time and keep it up to date with the latest changes in the game.*

## Usefulness

- Tracks and notifies you of in-game events of simple but highly useful events and its details. 

- Keep track of player names, time/date, weapon used, ship used of players and NPC have killed or that had killed you

- Works with any version (LIVE, PTU, etc..)

- Works in Persistent Universe and Arena Commander Modes 

## Screenshots

<div style="display: flex; flex-wrap: wrap; gap: 10px;">
  <a href="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/1.png?raw=true" target="_blank">
    <img src="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/1.png?raw=true" width="200">
  </a>
  <a href="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/2.png?raw=true" target="_blank">
    <img src="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/2.png?raw=true" width="200">
  </a>
  <a href="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/3.png?raw=true" target="_blank">
    <img src="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/3.png?raw=true" width="200">
  </a>
  <a href="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/4.png?raw=true" target="_blank">
    <img src="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/4.png?raw=true" width="200">
  </a>
  <a href="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/5.png?raw=true" target="_blank">
    <img src="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/5.png?raw=true" width="200">
  </a>
  <a href="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/6.png?raw=true" target="_blank">
    <img src="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/6.png?raw=true" width="200">
  </a>
  <a href="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/7.png?raw=true" target="_blank">
    <img src="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/7.png?raw=true" width="200">
  </a>
  <a href="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/8.png?raw=true" target="_blank">
    <img src="https://github.com/PINKgeekPDX/VerseWatcher/blob/main/preview/8.png?raw=true" width="200">
  </a>
</div>

## Features

- 🎯 Detailed kill/death event tracking

- 🔔 Kill event notifications

- 🔍 Event filtering and notifications

- 🔄 Session history and event details

- 🔄 Party/Team management and member tracking with notifications

- 📊 App session persistent historical timeline records of events kept


## Install options

- 📦 Pre-built executable .exe included in [Releases](https://github.com/PINKgeekPDX/VerseWatcher/releases) (recommended and easiest)

- 📦 Source code (if you are familure with python and want to make changes or just run the source or do it your way)

- 📦 I have developed a very robust and easy to use batch file to handle building the app and signs it with secured certificate if your windows defender is blocking the .exe or other issues, doing this way will solve all the issues by use of self signed certificate. It automates the ENTIRE processs and all steps. (I spent more time making this build and sign process then I care to admit, but it works well lol!)

All methods have more in depth details below.


## App Usage

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

## Requirements

- This app
- Star Citizen
- Python 3.8 or higher (if you aren't running from the .exe)
- 100MB free disk space

## Installation

### Option 1: Running from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/PINKgeekPDX/VerseWatcher.git
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

1. Download the latest release from the [Releases](https://github.com/PINKgeekPDX/VerseWatcher/releases) page
2. Extract the ZIP file to your desired location
3. Run `VerseWatcher.exe`

## Building and Signing the Application

### Prerequisites
- Windows 10 or later
- PowerShell 5.1 or later
- Python 3.8 or higher
- Administrator privileges (for certificate installation)

### Build Process

The application uses an automated build and sign process:

1. **Using BUILD-START.bat**
   ```batch
   BUILD-START.bat [options]
   ```
   Available options:
   - `clean` - Clean all build artifacts before building
   - `force` - Force rebuild everything
   - `debug` - Enable debug mode for detailed output
   - `skipSign` - Skip executable signing

   Examples:
   ```batch
   BUILD-START.bat
   BUILD-START.bat clean
   BUILD-START.bat clean force
   BUILD-START.bat debug skipSign
   ```

   The script will automatically:
   - Check for required software (PowerShell and Python)
   - Install required dependencies
   - Clean previous builds (if requested)
   - Build the executable using PyInstaller
   - Handle the signing process
   - Generate detailed build reports

2. **Automatic Signing Process**
   The signing process will:
   - Create a self-signed certificate if none exists
   - Install the certificate in the trusted root store
   - Sign the executable with timestamp
   - Verify the signature

### Build Reports
Detailed reports are automatically generated for every build:
- Location: `.\build\reports\build_[success/fail]_[TIMESTAMP].txt`
- Contains:
  - Build configuration and environment details
  - Complete build log
  - Signing details and certificate information
  - Any warnings or errors encountered
  - Build duration and final status
  - Troubleshooting suggestions (if build fails)

### Certificate Details
- Type: Code Signing Certificate
- Validity: 5 years
- Store Location: CurrentUser\My
- Trust Store: LocalMachine\Root
- Auto-renewed: No (manual renewal needed)

#### Common Issues:

1. **Certificate Trust Warnings**
   - Run BUILD-START.bat as administrator
   - Check build reports for certificate installation details
   - Verify certificate is properly installed in trusted root

2. **Build Failures**
   - Check build reports for detailed error messages
   - Verify Python 3.8+ is installed and in PATH
   - Ensure all dependencies are installed
   - Try running with `clean` and `force` options
   - Run in `debug` mode for more detailed output

3. **Signing Failures**
   - Run as administrator
   - Check build reports for specific error messages
   - Try with `skipSign` option if needed for testing

### Security Notes
- The application is signed with a self-signed certificate
- First-time users may see a Windows SmartScreen warning
- Certificate details are included in build reports
- Users can verify the signature in file properties

### For Developers
To manually build without the batch file:
1. Clean the environment:
   ```batch
   rmdir /s /q dist build
   ```

2. Run the PowerShell script directly:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "build\tools\sign-and-build.ps1" [-Clean] [-Force] [-DebugMode] [-SkipSign]
   ```

### Report Management
- Build reports are stored in `build\reports`
- Each build creates a new timestamped report
- Reports are named based on build status:
  - Success: `build_success_YYYYMMDD_HHMMSS.txt`
  - Failure: `build_fail_YYYYMMDD_HHMMSS.txt`
- Reports can be viewed through the BUILD-START.bat menu or directly in any text editor

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## FYI!

- This app does not interfere with your game in any way. 
- It will not be flagged by Anti cheat as it is totally passive.
- Using this does not violate TOS whatsoever.

## Windows Defender Warnings

VerseWatcher is built using PyInstaller, which can sometimes trigger false positives in Windows Defender. This is common for Python applications and does not indicate any actual security risk. Here's how to handle it:

### Verifying the Application
1. Each release includes a `checksum.txt` file containing the SHA256 hash of the executable
2. You can verify the file hasn't been tampered with by running this in PowerShell:
   ```powershell
   Get-FileHash "path\to\VerseWatcher.exe" -Algorithm SHA256
   ```
3. Compare the hash with the one in `checksum.txt`

### Adding an Exception
If Windows Defender is blocking the application:
1. Open Windows Security
2. Go to "Virus & threat protection"
3. Click "Manage settings" under "Virus & threat protection settings"
4. Scroll down to "Exclusions" and click "Add or remove exclusions"
5. Click "Add an exclusion" and choose "File"
6. Select the VerseWatcher.exe file

### Why These Warnings Happen
- Windows Defender sometimes flags Python applications as suspicious because they're packaged as standalone executables
- This is a known issue with PyInstaller and affects many legitimate Python applications
- VerseWatcher is open source, and you can verify the code and build process yourself
