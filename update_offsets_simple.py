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
GITHUB_CLIENT_DLL_URL = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json"
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


def get_nested_value(data, path):
    """Read a nested dict value by path, returning None when missing."""
    current = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def extract_required_offsets(remote_offsets, remote_client_dll):
    """Extract required offsets from nested cs2-dumper outputs."""
    if not isinstance(remote_offsets, dict):
        raise ValueError("Remote offsets payload is not a JSON object")
    if not isinstance(remote_client_dll, dict):
        raise ValueError("Remote client_dll payload is not a JSON object")

    source_paths = {
        "dwViewMatrix": ("offsets", ["client.dll", "dwViewMatrix"]),
        "dwLocalPlayerPawn": ("offsets", ["client.dll", "dwLocalPlayerPawn"]),
        "dwEntityList": ("offsets", ["client.dll", "dwEntityList"]),
        "m_hPlayerPawn": (
            "client_dll",
            ["client.dll", "classes", "CCSPlayerController", "fields", "m_hPlayerPawn"],
        ),
        "m_iHealth": ("client_dll", ["client.dll", "classes", "C_BaseEntity", "fields", "m_iHealth"]),
        "m_lifeState": (
            "client_dll",
            ["client.dll", "classes", "C_BaseEntity", "fields", "m_lifeState"],
        ),
        "m_iTeamNum": ("client_dll", ["client.dll", "classes", "C_BaseEntity", "fields", "m_iTeamNum"]),
        "m_vOldOrigin": (
            "client_dll",
            ["client.dll", "classes", "C_BasePlayerPawn", "fields", "m_vOldOrigin"],
        ),
        "m_pGameSceneNode": (
            "client_dll",
            ["client.dll", "classes", "C_BaseEntity", "fields", "m_pGameSceneNode"],
        ),
        "m_modelState": (
            "client_dll",
            ["client.dll", "classes", "CSkeletonInstance", "fields", "m_modelState"],
        ),
        "m_nodeToWorld": (
            "client_dll",
            ["client.dll", "classes", "CGameSceneNode", "fields", "m_nodeToWorld"],
        ),
        "m_sSanitizedPlayerName": (
            "client_dll",
            ["client.dll", "classes", "CCSPlayerController", "fields", "m_sSanitizedPlayerName"],
        ),
    }

    extracted = {}
    missing = []

    for offset_name, (source, path) in source_paths.items():
        source_data = remote_offsets if source == "offsets" else remote_client_dll
        value = get_nested_value(source_data, path)
        if value is None:
            missing.append(f"{offset_name} ({source}:{'.'.join(path)})")
            continue
        extracted[offset_name] = coerce_offset_value(offset_name, value)

    # In current dumps this is an offset inside CModelState and remains stable.
    bone_array_value = get_nested_value(
        remote_client_dll,
        ["client.dll", "classes", "CModelState", "fields", "m_boneArray"],
    )
    if bone_array_value is None:
        bone_array_value = 0x80
    extracted["m_boneArray"] = coerce_offset_value("m_boneArray", bone_array_value)

    missing_required = sorted(REQUIRED_OFFSETS - set(extracted.keys()))
    if missing_required or missing:
        details = ", ".join(missing + missing_required)
        raise ValueError(f"Missing required offsets: {details}")

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
        # Upstream switched from `build` to `build_number`; support both.
        build = data.get('build_number', data.get('build'))
        if build is None:
            raise ValueError(f"Missing build field in info.json (keys: {list(data.keys())})")
        return int(build)
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
        offsets_response = requests.get(GITHUB_OFFSETS_URL, timeout=5)
        offsets_response.raise_for_status()
        remote_offsets = offsets_response.json()

        client_dll_response = requests.get(GITHUB_CLIENT_DLL_URL, timeout=5)
        client_dll_response.raise_for_status()
        remote_client_dll = client_dll_response.json()
        
        # Validate schema and extract only required keys.
        updated_offsets = extract_required_offsets(remote_offsets, remote_client_dll)
        
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
                if remote_build is not None:
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
