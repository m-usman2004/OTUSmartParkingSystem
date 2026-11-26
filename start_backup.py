import os
import sys
import subprocess
from pathlib import Path

# Gets the root project directory
BASE_DIR = Path(__file__).resolve().parent

# Path to the central server application
CENTRAL_SERVER = BASE_DIR / "central_server" / "app.py"

# Run the same central server code on port 5100 as the backup
env = os.environ.copy()
env["CENTRAL_PORT"] = "5100"

print("Starting backup central server on port 5100...")

try:
    subprocess.run([sys.executable, str(CENTRAL_SERVER)], env=env, cwd=BASE_DIR)
except KeyboardInterrupt:
    print("\nBackup central server stopped.")
