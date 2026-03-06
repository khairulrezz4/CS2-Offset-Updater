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


def cs2_is_running():
    """Check if CS2 is running"""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] in ['cs2.exe', 'cs2go.exe']:
            return True
    return False


def get_remote_build():
    """Fetch current build number from GitHub"""
    try:
        response = requests.get(GITHUB_INFO_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('build', 0)
    except Exception as e:
        print(f"❌ Failed to fetch build info: {e}")
        return None


def get_local_build():
    """Get cached build number"""
    if CACHE_FILE.exists():
        try:
            return int(CACHE_FILE.read_text().strip())
        except:
            return None
    return None


def update_offsets():
    """Fetch and update only the 13 essential offsets"""
    try:
        print("📡 Fetching offsets from GitHub...")
        response = requests.get(GITHUB_OFFSETS_URL, timeout=5)
        response.raise_for_status()
        remote_offsets = response.json()
        
        # Extract only required offsets
        updated_offsets = {}
        missing = []
        
        for offset_name in REQUIRED_OFFSETS:
            if offset_name in remote_offsets:
                # Convert to int if it's a string (hex or decimal)
                value = remote_offsets[offset_name]
                if isinstance(value, str):
                    if value.startswith('0x'):
                        value = int(value, 16)
                    else:
                        value = int(value)
                updated_offsets[offset_name] = value
            else:
                missing.append(offset_name)
        
        if missing:
            print(f"⚠️  Missing offsets: {', '.join(missing)}")
        
        # Save to file
        OFFSETS_FILE.write_text(json.dumps(updated_offsets, indent=2))
        print(f"✓ Updated {len(updated_offsets)} offsets")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fetch offsets: {e}")
        return False


def main():
    """Main monitoring loop"""
    print("🎮 CS2 Offset Updater (Simple - 13 offsets)")
    print("Watching for CS2 launch...\n")
    
    cs2_was_running = False
    
    while True:
        is_running = cs2_is_running()
        
        # Detect CS2 launch (transition from not running to running)
        if is_running and not cs2_was_running:
            local_build = get_local_build()
            remote_build = get_remote_build()
            
            if local_build != remote_build:
                print(f"🎮 CS2 launched at {time.strftime('%H:%M:%S')}")
                if remote_build:
                    print(f"Build mismatch: Local={local_build}, Remote={remote_build}")
                    if update_offsets():
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
