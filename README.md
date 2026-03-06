# Offset Updater (Simple)

This project keeps `offsets.json` up to date using `update_offsets_simple.py`.

## Disclaimer

This project is provided for educational and research purposes only. Use is at your own risk, and users are responsible for complying with all applicable laws, terms of service, and platform rules. The author is not liable for any issues, damages, or losses that occur during installation or use.

It tracks only these 13 fields:

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

## Files

- `update_offsets_simple.py`: main updater script
- `offsets.json`: output file updated by the script
- `requirements.txt`: Python dependencies

## Installation

This offset is to update offset for this ESP: [Download here](https://www.unknowncheats.me/forum/downloads.php?do=file&id=51609)

1. Download or clone this repository.
2. Open a terminal in the `ESP` folder.
3. Install dependencies:

```bash
pip install psutil requests
```

You can also use:

```bash
pip install -r requirements.txt
```

## Usage

Run the updater:

```bash
python update_offsets_simple.py
```

The script will:

1. Watch for `cs2.exe` or `cs2go.exe`.
2. Check the latest build metadata.
3. Download new offsets only when build changes.
4. Save only the 13 required fields into `offsets.json`.

Stop the script with `Ctrl+C`.

## Expected Output

Typical startup logs:

```text
CS2 Offset Updater (Simple - 13 offsets)
Watching for CS2 launch...
```

On update:

```text
CS2 launched at HH:MM:SS
Build mismatch: Local=..., Remote=...
Fetching offsets from GitHub...
Updated 13 offsets
```

## Troubleshooting

- `ModuleNotFoundError: No module named 'psutil'`:
   Run `pip install psutil requests`.
- `Failed to fetch build info` or `Failed to fetch offsets`:
   Check internet access and retry.
- No updates happening:
   Make sure the process name is `cs2.exe` or `cs2go.exe`.
- Script exits unexpectedly:
   Run again and check terminal output for the exact error.

## Notes

- Build caching is stored in `.build_cache`.
- `offsets.json` is written in decimal format.
- If a required key is missing upstream, the script prints a warning.

Educational use only. You are responsible for complying with all applicable rules, terms, and laws. The author is not liable for any issues, damages, or losses that occur during installation or use.
