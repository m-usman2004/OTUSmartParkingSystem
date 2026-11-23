
import os
import sys
import subprocess
from pathlib import Path
from lots_config import LOT_CONFIG

# Gets the root project directory
BASE_DIR = Path(__file__).resolve().parent

# Path to the parking lot server application
LOT_SERVER = BASE_DIR / "lot_server" / "app.py"

processes = []

try:
    # Start a separate Flask process for each parking lot
    for lot_id, config in LOT_CONFIG.items():

        # Copy the current environment variables
        env = os.environ.copy()

        # Configure this parking lot's ID, port, and capacity
        env["LOT_ID"] = lot_id
        env["PORT"] = str(config["port"])
        env["LOT_CAPACITY"] = str(config["capacity"])

        # Start the parking lot server as an independent process
        process = subprocess.Popen(
            [sys.executable, str(LOT_SERVER)],
            env=env,
            cwd=BASE_DIR
        )

        processes.append(process)

        print(f"Started Lot {lot_id} on port {config['port']}")

    print("\nAll parking lot servers started. Press Ctrl+C to stop them.")

    # Keep the script running while the lot servers operate
    for process in processes:
        process.wait()

except KeyboardInterrupt:
    print("\nStopping parking lot servers...")

finally:
    # Stop any remaining parking lot processes
    for process in processes:
        if process.poll() is None:
            process.terminate()

    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    print("Parking lot servers stopped.")
