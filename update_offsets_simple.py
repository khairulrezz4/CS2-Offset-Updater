"""
Simple Offset Updater - Auto-updates only essential 13 offsets from GitHub
Monitors for CS2 launch and fetches latest offsets automatically
"""

import json
import time
import requests
import psutil
from pathlib import Path

# Configuration
GITHUB_OFFSETS_URL = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json"
GITHUB_INFO_URL = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/info.json"
OFFSETS_FILE = Path(__file__).parent / "offsets.json"

# Only these 13 offsets will be extracted
REQUIRED_OFFSETS = {
    "dwViewMatrix",
    "dwLocalPlayerPawn",
    "dwEntityList",
    "m_hPlayerPawn",
    "m_iHealth",
    "m_lifeState",
    "m_iTeamNum",
    "m_vOldOrigin",
    "m_pGameSceneNode",
    "m_modelState",
    "m_boneArray",
    "m_nodeToWorld",
    "m_sSanitizedPlayerName",
}

CACHE_FILE = Path(__file__).parent / ".build_cache"


def coerce_offset_value(offset_name, value):
    """Convert offset value to int and reject invalid ranges."""
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned.startswith("0x"):
            parsed = int(cleaned, 16)
        else:
            parsed = int(cleaned)
    else:
        raise ValueError(f"{offset_name} must be int or numeric string")

    # Offsets are expected to be non-negative integer addresses/field offsets.
    if parsed < 0 or parsed > 0x7FFFFFFF:
        raise ValueError(f"{offset_name} has out-of-range value: {parsed}")

    return parsed


def extract_required_offsets(remote_offsets):
    """Validate remote payload and return only required offset keys."""
    if not isinstance(remote_offsets, dict):
        raise ValueError("Remote offsets payload is not a JSON object")

    missing = sorted(REQUIRED_OFFSETS - set(remote_offsets.keys()))
    if missing:
        raise ValueError(f"Missing required offsets: {', '.join(missing)}")

    extracted = {}
    for offset_name in REQUIRED_OFFSETS:
        extracted[offset_name] = coerce_offset_value(offset_name, remote_offsets[offset_name])

    return extracted


def write_offsets_atomically(offsets_data):
    """Write offsets.json safely to avoid partial/corrupted writes."""
    temp_path = OFFSETS_FILE.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(offsets_data, indent=2), encoding="utf-8")
    temp_path.replace(OFFSETS_FILE)


def cs2_is_running():
    """Check if CS2 is running"""
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info.get('name')
            if name in ['cs2.exe', 'cs2go.exe']:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def get_remote_build():
    """Fetch current build number from GitHub"""
    try:
        response = requests.get(GITHUB_INFO_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('build', 0)
    except requests.RequestException as e:
        print(f"❌ Failed to fetch build info: {e}")
        return None
    except ValueError as e:
        print(f"❌ Invalid build info JSON: {e}")
        return None


def get_local_build():
    """Get cached build number"""
    # Cache avoids unnecessary downloads when offsets are already current.
    if CACHE_FILE.exists():
        try:
            return int(CACHE_FILE.read_text().strip())
        except (ValueError, OSError):
            return None
    return None


def update_offsets():
    """Fetch and update only the 13 essential offsets"""
    try:
        print("📡 Fetching offsets from GitHub...")
        response = requests.get(GITHUB_OFFSETS_URL, timeout=5)
        response.raise_for_status()
        remote_offsets = response.json()
        
        # Validate schema and extract only required keys.
        updated_offsets = extract_required_offsets(remote_offsets)
        
        # Write a clean JSON file containing only the required keys.
        write_offsets_atomically(updated_offsets)
        print(f"✓ Updated {len(updated_offsets)} offsets")
        return True
        
    except requests.RequestException as e:
        print(f"❌ Failed to fetch offsets: {e}")
        return False
    except ValueError as e:
        print(f"❌ Invalid offset data: {e}")
        return False
    except OSError as e:
        print(f"❌ Failed to fetch offsets: {e}")
        return False


def main():
    """Main monitoring loop"""
    print("🎮 CS2 Offset Updater (Simple - 13 offsets)")
    print("Watching for CS2 launch...\n")
    
    cs2_was_running = False
    
    while True:
        is_running = cs2_is_running()
        
        # Trigger update only on launch edge (False -> True), not every loop.
        if is_running and not cs2_was_running:
            local_build = get_local_build()
            remote_build = get_remote_build()
            
            # Update only when a new upstream build is available.
            if local_build != remote_build:
                print(f"🎮 CS2 launched at {time.strftime('%H:%M:%S')}")
                if remote_build:
                    print(f"Build mismatch: Local={local_build}, Remote={remote_build}")
                    if update_offsets():
                        # Persist build number so future launches skip redundant updates.
                        CACHE_FILE.write_text(str(remote_build))
                        print("✓ Offsets updated to latest\n")
                    else:
                        print("Failed to update offsets\n")
                else:
                    print("Could not fetch remote build info\n")
            else:
                print(f"🎮 CS2 launched at {time.strftime('%H:%M:%S')}")
                print(f"✓ Offsets up to date (Build: {local_build})\n")
        
        cs2_was_running = is_running
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Offset updater stopped")
