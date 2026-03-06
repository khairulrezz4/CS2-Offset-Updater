"""
ESP Launcher - Runs offset monitor and ESP together
"""

import subprocess
import sys
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
MAIN_ESP = SCRIPT_DIR / "cs2go.exe"
MONITOR_SCRIPT = SCRIPT_DIR / "update_offsets_monitor.py"
RUN_SCRIPT = SCRIPT_DIR / "run.py"


def check_dependencies():
    """Check if required packages are installed"""
    try:
        import psutil
        import requests
    except ImportError:
        print("❌ Missing dependencies. Installing...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "-q", "psutil", "requests"
        ])
        print("✅ Dependencies installed")


def main():
    """Launch the ESP system"""
    print("=" * 60)
    print("CS2 ESP System - Launcher")
    print("=" * 60)
    
    print("\n🔧 Checking dependencies...")
    check_dependencies()
    
    print("\n📋 Starting services:")
    print("   1. Offset Auto-Update Monitor")
    print("   2. ESP Control (run.py)")
    print("\n" + "-" * 60)
    
    try:
        # Start offset monitor in background
        print("\n🚀 Starting offset monitor...")
        monitor_proc = subprocess.Popen(
            [sys.executable, str(MONITOR_SCRIPT)],
            # Keep window visible for monitoring
        )
        print(f"   Monitor PID: {monitor_proc.pid}")
        
        # Start ESP control script
        print("\n🎮 Starting ESP control...")
        run_proc = subprocess.Popen(
            [sys.executable, str(RUN_SCRIPT)],
        )
        print(f"   Control PID: {run_proc.pid}")
        
        print("\n" + "-" * 60)
        print("✅ All services started!")
        print("\nControls:")
        print("  - INSERT: Toggle ESP on/off")
        print("  - L-ALT:  Force on (hold)")
        print("\n Press Ctrl+C to stop all services...\n")
        
        # Wait for both processes
        monitor_proc.wait()
        run_proc.wait()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Shutting down...")
        try:
            monitor_proc.terminate()
            run_proc.terminate()
            monitor_proc.wait(timeout=2)
            run_proc.wait(timeout=2)
        except:
            pass
        print("✅ Services stopped")


if __name__ == "__main__":
    main()
