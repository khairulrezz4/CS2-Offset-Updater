# Offset Updater (Simple)

Small Python updater that keeps `offsets.json` current for the linked ESP project.

This updater is intended for this ESP build:
[Download here](https://www.unknowncheats.me/forum/downloads.php?do=file&id=51609)

## What It Does

- Watches for `cs2.exe` / `cs2go.exe` launch.
- Checks remote build metadata.
- Updates only when the upstream build changes.
- Writes only the 13 required offsets to `offsets.json`.

## Quick Start

1. Open a terminal in the `ESP` folder.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the updater:

```bash
python update_offsets_simple.py
```

4. Leave it running. Stop with `Ctrl+C`.

## Project Files

- `update_offsets_simple.py`: main updater script
- `offsets.json`: output file written by the updater
- `requirements.txt`: Python dependencies
- `.build_cache`: local file storing last known build

## Required Offset Keys

The updater writes only these fields:

- `dwViewMatrix`
- `dwLocalPlayerPawn`
- `dwEntityList`
- `m_hPlayerPawn`
- `m_iHealth`
- `m_lifeState`
- `m_iTeamNum`
- `m_vOldOrigin`
- `m_pGameSceneNode`
- `m_modelState`
- `m_boneArray`
- `m_nodeToWorld`
- `m_sSanitizedPlayerName`

## Expected Output

Startup:

```text
CS2 Offset Updater (Simple - 13 offsets)
Watching for CS2 launch...
```

When an update is needed:

```text
CS2 launched at HH:MM:SS
Build mismatch: Local=..., Remote=...
Fetching offsets from GitHub...
Updated 13 offsets
```

## Troubleshooting

- `ModuleNotFoundError: No module named 'psutil'`
   - Run `pip install -r requirements.txt`
- `Failed to fetch build info` or `Failed to fetch offsets`
   - Check internet access, then retry
- No updates happen on launch
   - Confirm process name is `cs2.exe` or `cs2go.exe`
- Script exits unexpectedly
   - Run again and check the exact terminal error

## Update History

### 2026-03-06

#### Added

- Support for `build_number` in upstream `info.json` (with fallback to legacy `build`).
- Fallback for `m_boneArray` to `0x80` when not present upstream.

#### Changed

- Extractor now supports the new cs2-dumper schema:
   - Reads module offsets from `output/offsets.json` under `client.dll`.
   - Reads netvars from `output/client_dll.json` class `fields`.

#### Fixed

- Launch-update check now treats missing remote build as `None` only.
- Validation now reports missing required offsets with clearer source/path context.

## Disclaimer

This project is provided for educational and research purposes only.
Use is at your own risk. You are responsible for complying with all applicable laws,
terms of service, and platform rules. The author is not liable for any issues,
damages, or losses that occur during installation or use.
