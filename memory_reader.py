"""
CS2 Memory Reader - Validates offsets by reading actual game memory
"""

import struct
import json
from pathlib import Path
import ctypes
from ctypes import wintypes, c_size_t
import ctypes.wintypes as wt

# Memory reading via ctypes
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
TH32CS_SNAPMODULE = 0x00000008

kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

# TLHelp32 structures
class MODULEENTRY32(ctypes.Structure):
    pass

MODULEENTRY32._fields_ = [
    ("dwSize", wt.DWORD),
    ("th32ModuleID", wt.DWORD),
    ("th32ProcessID", wt.DWORD),
    ("GlblcntUsage", wt.DWORD),
    ("ProccntUsage", wt.DWORD),
    ("modBaseAddr", ctypes.c_void_p),
    ("modBaseSize", wt.DWORD),
    ("hModule", wt.HMODULE),
    ("szModule", wt.CHAR * 256),
    ("szExePath", wt.CHAR * 260),
]

OFFSETS_FILE = Path(__file__).parent / "offsets.json"


class MemoryReader:
    """Read memory from a process"""
    
    def __init__(self, process_name="cs2.exe"):
        self.process_name = process_name
        self.pid = None
        self.handle = None
        self.module_base = None
        self.offsets = self._load_offsets()
    
    def _load_offsets(self):
        """Load offsets from JSON file"""
        try:
            with open(OFFSETS_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Offsets file not found: {OFFSETS_FILE}")
            return {}
    
    def _get_module_base(self, module_name="client.dll"):
        """Get the base address of a loaded module using TLHelp32"""
        try:
            # Create tool help snapshot
            hSnapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, self.pid)
            if hSnapshot == -1:
                return None
            
            me32 = MODULEENTRY32()
            me32.dwSize = ctypes.sizeof(MODULEENTRY32)
            
            # Get first module
            if kernel32.Module32First(hSnapshot, ctypes.byref(me32)):
                while True:
                    mod_name = me32.szModule.decode('utf-8', errors='ignore').lower()
                    if module_name.lower() in mod_name:
                        base_addr = ctypes.cast(me32.modBaseAddr, ctypes.c_void_p).value
                        kernel32.CloseHandle(hSnapshot)
                        return base_addr
                    
                    # Get next module
                    if not kernel32.Module32Next(hSnapshot, ctypes.byref(me32)):
                        break
            
            kernel32.CloseHandle(hSnapshot)
        except Exception as e:
            print(f"⚠️  Module base lookup error: {e}")
        
        return None
    
    def connect(self):
        """Connect to CS2 process"""
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'].lower() == self.process_name.lower():
                    self.pid = proc.info['pid']
                    break
            
            if not self.pid:
                print(f"❌ Process not found: {self.process_name}")
                return False
            
            # Open process
            self.handle = kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                False,
                self.pid
            )
            
            if not self.handle:
                print(f"❌ Failed to open process: {self.process_name}")
                return False
            
            # Get client.dll base address
            self.module_base = self._get_module_base("client.dll")
            if not self.module_base:
                print("⚠️  Warning: Could not determine client.dll base address")
            
            print(f"✅ Connected to {self.process_name} (PID: {self.pid})")
            if self.module_base:
                print(f"   client.dll base: 0x{self.module_base:08x}")
            return True
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def read_memory(self, address, size):
        """Read bytes from process memory"""
        try:
            if not self.handle:
                return None
            
            buffer = ctypes.create_string_buffer(size)
            bytes_read = c_size_t()
            
            result = kernel32.ReadProcessMemory(
                self.handle,
                ctypes.c_void_p(address),
                buffer,
                size,
                ctypes.byref(bytes_read)
            )
            
            if not result:
                # Debug: get error code
                error = kernel32.GetLastError()
                # print(f"  [ReadProcessMemory error: {error}]")
                return None
            
            if bytes_read.value != size:
                # print(f"  [Partial read: {bytes_read.value}/{size}]")
                return None
                
            return buffer.raw[:bytes_read.value]
            
        except Exception as e:
            # print(f"  [Exception: {e}]")
            return None
    
    def read_int(self, address):
        """Read 32-bit integer"""
        data = self.read_memory(address, 4)
        return struct.unpack("<I", data)[0] if data else None
    
    def read_float(self, address):
        """Read 32-bit float"""
        data = self.read_memory(address, 4)
        return struct.unpack("<f", data)[0] if data else None
    
    def read_string(self, address, max_length=64):
        """Read null-terminated string"""
        try:
            data = self.read_memory(address, max_length)
            if data:
                return data.split(b'\x00')[0].decode('utf-8', errors='ignore')
        except:
            pass
        return None
    
    def validate_offsets(self):
        """Validate offsets by reading key values"""
        if not self.handle:
            print("❌ Not connected to process")
            return False
        
        print("\n" + "="*50)
        print("Validating Offsets")
        print("="*50)
        
        tests_passed = 0
        tests_total = 0
        
        # Offsets from the JSON might be absolute locations in client.dll
        # Try with AND without module base
        
        if "dwViewMatrix" in self.offsets:
            tests_total += 1
            offset = self.offsets["dwViewMatrix"]
            
            # Try direct offset first
            print(f"\n  dwViewMatrix offset: 0x{offset:08x}")
            val = self.read_int(offset)
            
            if val and val != 0:
                print(f"    ✅ Direct read: 0x{val:08x}")
                tests_passed += 1
            elif self.module_base:
                # Try with module base
                addr = self.module_base + offset
                print(f"    Trying module base + offset: 0x{addr:016x}")
                val = self.read_int(addr)
                if val and val != 0:
                    print(f"    ✅ With module base: 0x{val:08x}")
                    tests_passed += 1
                else:
                    print(f"    ❌ Neither method worked")
            else:
                print(f"    ❌ Direct read failed, no module base")
        
        # Try to read entity list pointer
        if "dwEntityList" in self.offsets:
            tests_total += 1
            offset = self.offsets["dwEntityList"]
            
            print(f"\n  dwEntityList offset: 0x{offset:08x}")
            val = self.read_int(offset)
            
            if val and val != 0:
                print(f"    ✅ Direct read: 0x{val:08x}")
                tests_passed += 1
            elif self.module_base:
                addr = self.module_base + offset
                print(f"    Trying module base + offset: 0x{addr:016x}")
                val = self.read_int(addr)
                if val and val != 0:
                    print(f"    ✅ With module base: 0x{val:08x}")
                    tests_passed += 1
                else:
                    print(f"    ❌ Neither method worked")
            else:
                print(f"    ❌ Direct read failed, no module base")
        
        # Try to read local player pawn
        if "dwLocalPlayerPawn" in self.offsets:
            tests_total += 1
            offset = self.offsets["dwLocalPlayerPawn"]
            
            print(f"\n  dwLocalPlayerPawn offset: 0x{offset:08x}")
            val = self.read_int(offset)
            
            if val and val != 0:
                print(f"    ✅ Direct read: 0x{val:08x}")
                tests_passed += 1
            elif self.module_base:
                addr = self.module_base + offset
                print(f"    Trying module base + offset: 0x{addr:016x}")
                val = self.read_int(addr)
                if val and val != 0:
                    print(f"    ✅ With module base: 0x{val:08x}")
                    tests_passed += 1
                else:
                    print(f"    ❌ Neither method worked")
            else:
                print(f"    ❌ Direct read failed, no module base")
        
        print("\n" + "="*50)
        print(f"Validation: {tests_passed}/{tests_total} tests passed")
        print("="*50 + "\n")
        
        if tests_passed == 0:
            print("⚠️  Offset validation failed. This is likely because:")
            print("   - Running without administrator privileges")
            print("   - Game data not loaded yet (wait a few seconds in-menu)")
            print("   - Offsets may be outdated\n")
            print("✓ This doesn't mean the monitor won't work - it will still")
            print("  auto-update offsets when CS2 launches.\n")
        
        return tests_passed > 0
    
    def disconnect(self):
        """Close process handle"""
        if self.handle:
            kernel32.CloseHandle(self.handle)
            self.handle = None


def main():
    """Test memory reader"""
    import time
    
    print("\n🔧 CS2 Memory Reader - Testing Offsets\n")
    
    reader = MemoryReader("cs2.exe")
    
    if reader.connect():
        time.sleep(1)  # Give time for reads
        reader.validate_offsets()
        reader.disconnect()
    else:
        print("❌ Failed to connect. Make sure CS2 is running!")


if __name__ == "__main__":
    main()
