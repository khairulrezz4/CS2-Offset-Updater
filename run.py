import subprocess
import keyboard  # pip install keyboard
import time
import threading

# --- CONFIGURATION ---
EXECUTABLE_PATH = r"C:\Projects\cs2\cs2go\cs2go.exe"  # ← change this

# --- STATE ---
process = None
running = False
insert_toggle = False
alt_held = False
monitor_thread = None


def monitor_process():
    """Monitor the process and restart it if it exits while running."""
    global process, running
    while True:
        if running:
            if process and process.poll() is not None:
                # Restart if process crashed while running
                process = subprocess.Popen(
                    [EXECUTABLE_PATH],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
        time.sleep(2)


def start_process():
    """Start the process silently."""
    global process, running
    if running:
        return

    running = True
    process = subprocess.Popen(
        [EXECUTABLE_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print("\rRUNNING ", end="", flush=True)


def stop_process():
    """Stop the process if running."""
    global process, running
    if not running:
        return

    running = False
    if process and process.poll() is None:
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            process.kill()
    print("\rSTOPPED ", end="", flush=True)


def update_state():
    """Update process state based on Insert toggle and Alt key."""
    global alt_held, insert_toggle

    if alt_held:
        # Alt always forces ON
        if not running:
            start_process()
    else:
        # When Alt is released, fall back to Insert toggle state
        if insert_toggle and not running:
            start_process()
        elif not insert_toggle and running:
            stop_process()


def on_insert(_):
    """Toggle Insert mode on/off."""
    global insert_toggle
    insert_toggle = not insert_toggle
    update_state()


def on_alt_press(_):
    """Left Alt pressed — force ON."""
    global alt_held
    alt_held = True
    update_state()


def on_alt_release(_):
    """Left Alt released — re-evaluate state."""
    global alt_held
    global insert_toggle
    insert_toggle = False
    alt_held = False
    update_state()


def main():
    global monitor_thread

    print("STOPPED ", end="", flush=True)

    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_process, daemon=True)
    monitor_thread.start()

    # Bind keys
    keyboard.on_press_key("insert", on_insert)
    keyboard.on_press_key("left alt", on_alt_press)
    keyboard.on_release_key("left alt", on_alt_release)

    try:
        keyboard.wait()  # Keeps running indefinitely
    except KeyboardInterrupt:
        stop_process()
        print("\nExiting.")


if __name__ == "__main__":
    main()
