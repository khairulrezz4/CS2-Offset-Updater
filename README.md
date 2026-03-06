# CS2 ESP Offset Auto-Update System

This system automatically fetches and updates CS2 offsets when the game launches.

## Files

- **`update_offsets_monitor.py`** - Main monitor script that watches for CS2 launch and updates offsets
- **`memory_reader.py`** - Memory validation tool to verify offsets are working
- **`launcher.py`** - All-in-one launcher that starts everything
- **`offsets.json`** - Current game offsets (auto-updated)
- **`run.py`** - ESP control script (Insert toggle, Alt force-on)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install psutil requests
```

### 2. Choose Your Setup

#### Option A: Easy Mode (Recommended)
Just run the launcher which starts everything:
```bash
python launcher.py
```

Controls:
- **INSERT** - Toggle ESP on/off when CS2 is not running
- **L-ALT** - Force ESP on (hold ALT, then launch CS2)

#### Option B: Run Monitor Only
If you only want auto-updating (without the ESP launcher):
```bash
python update_offsets_monitor.py
```

Then manually run `cs2go.exe`

#### Option C: Manual Updates
Run the main updater script:
```bash
python ../hello.py
```

## How It Works

1. **Monitor Detects CS2 Launch**
   - Continuously watches for `cs2.exe` or `cs2go.exe` process
   - Checks every 2 seconds

2. **Fetches Latest Offsets from GitHub**
   - Gets offsets from https://github.com/a2x/cs2-dumper
   - Compares build number to avoid unnecessary updates
   - Only updates if there's a new CS2 build

3. **Updates offsets.json**
   - Writes new offsets to `offsets.json`
   - Also updates parent folder's `offsets.json`
   - Caches build number to avoid repeated fetches

## Validating Offsets

After CS2 launches, you can validate that offsets are working:

```bash
python memory_reader.py
```

This will attempt to read actual memory from CS2 using the offsets and show:
- ✅ if the offset is valid and reading data
- ❌ if the offset is invalid or not accessible

## Troubleshooting

### "CS2 process not found"
- Make sure CS2 is running
- Check if it's named `cs2.exe` or `cs2go.exe`

### "Failed to fetch offsets from GitHub"
- Check your internet connection
- The GitHub API might be temporarily unavailable

### "Missing dependencies"
- Run: `pip install psutil requests`

### Memory reader shows ❌
- Offsets might be outdated
- Try running again after CS2 fully loads
- Run the monitor to fetch the latest offsets

## Manual Offset Updates

If you want to force an update without launching CS2:

```bash
cd ..
python hello.py
```

This will fetch the latest offsets and copy them to the ESP folder.

## Auto-Start on Boot (Windows)

Create a batch file `start_esp.bat`:
```batch
@echo off
cd /d "%~dp0"
python launcher.py
```

Add it to your Startup folder:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
```

## Notes

- The monitor runs indefinitely. Press Ctrl+C to stop.
- Offsets are automatically validated for missing fields
- Build cache prevents unnecessary GitHub API calls
- Memory reader requires admin privileges to read game memory

## Latest Offsets

Build: 14137
- dwViewMatrix: 36749024
- dwLocalPlayerPawn: 33970928
- dwEntityList: 38449592
- m_iHealth: 852
- And 9 more offsets...

See `offsets.json` for the complete list.
