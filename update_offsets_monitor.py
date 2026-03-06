"""
Auto-update offsets when CS2 launches
Monitors CS2 process and fetches latest offsets from GitHub dumper
"""

import json
import requests
import os
import time
import psutil
from pathlib import Path

# Configuration
INFO_URL = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/info.json"
OFFSETS_URL = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json"
CLIENT_URL = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json"

SCRIPT_DIR = Path(__file__).parent
OFFSETS_FILE = SCRIPT_DIR / "offsets.json"
BUILD_FILE = SCRIPT_DIR / ".build_cache"

CS2_PROCESSES = ["cs2.exe", "cs2go.exe"]
CHECK_INTERVAL = 2  # seconds


def safe_get(obj, *keys, default=None):
    """Safely read nested JSON fields"""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key)
        else:
            return default
    return obj if obj is not None else default


def get_json(url):
    """Fetch JSON from URL"""
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return None


def get_remote_build():
    """Get remote CS2 build number"""
    try:
        data = get_json(INFO_URL)
        return int(data.get("build_number", 0)) if data else 0
    except Exception as e:
        print(f"❌ Error getting remote build: {e}")
        return 0


def get_local_build():
    """Get cached local build number"""
    if BUILD_FILE.exists():
        try:
            with open(BUILD_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0


def save_build(build):
    """Save build number to cache"""
    try:
        with open(BUILD_FILE, "w") as f:
            f.write(str(build))
    except Exception as e:
        print(f"⚠️  Could not save build cache: {e}")


def update_offsets():
    """Fetch and save latest offsets"""
    try:
        print("\n📥 Fetching latest offsets from GitHub...")
        
        offsets = get_json(OFFSETS_URL)
        client = get_json(CLIENT_URL)
        
        if not offsets or not client:
            print("❌ Failed to fetch offset data")
            return False
        
        classes = safe_get(client, "client.dll", "classes", default={})
        m_iHealth_alt = safe_get(classes, "C_CSPlayerPawn", "fields", "m_iHealth")
        m_lifeState_alt = safe_get(classes, "C_CSPlayerPawn", "fields", "m_lifeState")
        
        result = {
            "dwViewMatrix": safe_get(offsets, "client.dll", "dwViewMatrix"),
            "dwLocalPlayerPawn": safe_get(offsets, "client.dll", "dwLocalPlayerPawn"),
            "dwEntityList": safe_get(offsets, "client.dll", "dwEntityList"),
            "m_hPlayerPawn": safe_get(classes, "CCSPlayerController", "fields", "m_hPlayerPawn"),
            "m_iHealth": m_iHealth_alt or safe_get(classes, "C_BaseEntity", "fields", "m_iHealth"),
            "m_lifeState": m_lifeState_alt or safe_get(classes, "C_BaseEntity", "fields", "m_lifeState"),
            "m_iTeamNum": safe_get(classes, "C_BaseEntity", "fields", "m_iTeamNum"),
            "m_vOldOrigin": safe_get(classes, "C_BasePlayerPawn", "fields", "m_vOldOrigin"),
            "m_pGameSceneNode": safe_get(classes, "C_BaseEntity", "fields", "m_pGameSceneNode"),
            "m_modelState": safe_get(classes, "CSkeletonInstance", "fields", "m_modelState", default=352),
            "m_boneArray": safe_get(classes, "CSkeletonInstance", "fields", "m_boneArray", default=128),
            "m_nodeToWorld": safe_get(classes, "CGameSceneNode", "fields", "m_nodeToWorld", default=16),
            "m_sSanitizedPlayerName": safe_get(classes, "CCSPlayerController", "fields", "m_sSanitizedPlayerName")
        }
        
        # Check for missing values
        missing_fields = [k for k, v in result.items() if v is None]
        if missing_fields:
            print(f"⚠️  Missing offsets: {', '.join(missing_fields)}")
            return False
        
        # Write to file
        with open(OFFSETS_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
        # Get new build number
        remote_build = get_remote_build()
        save_build(remote_build)
        
        print(f"✅ Offsets updated successfully (Build: {remote_build})")
        print(f"   Saved to: {OFFSETS_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating offsets: {e}")
        return False


def cs2_is_running():
    """Check if CS2 process is running"""
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() in [p.lower() for p in CS2_PROCESSES]:
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False


def wait_for_cs2():
    """Wait for CS2 to launch"""
    print("⏳ Waiting for CS2 to launch...")
    while not cs2_is_running():
        time.sleep(CHECK_INTERVAL)
    print("✅ CS2 detected!")


def wait_for_cs2_exit():
    """Wait for CS2 to exit"""
    while cs2_is_running():
        time.sleep(CHECK_INTERVAL)


def main():
    """Main monitoring loop"""
    print("=" * 50)
    print("CS2 Offset Auto-Update Monitor")
    print("=" * 50)
    
    cs2_was_running = False
    
    while True:
        is_running = cs2_is_running()
        
        if is_running and not cs2_was_running:
            # CS2 just launched
            print(f"\n🎮 CS2 launched at {time.strftime('%H:%M:%S')}")
            
            # Check if offsets need updating
            remote_build = get_remote_build()
            local_build = get_local_build()
            
            if remote_build == 0:
                print("⚠️  Could not reach GitHub, keeping current offsets")
            elif remote_build != local_build:
                print(f"📊 Local build: {local_build}, Remote build: {remote_build}")
                update_offsets()
            else:
                print(f"✓ Offsets up to date (Build: {remote_build})")
            
            cs2_was_running = True
            
        elif not is_running and cs2_was_running:
            # CS2 just exited
            print(f"\n❌ CS2 closed at {time.strftime('%H:%M:%S')}")
            cs2_was_running = False
        
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped")
