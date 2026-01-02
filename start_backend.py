import subprocess
import sys
import os

def start_backend():
    env = os.environ.copy()
    print("Starting FastAPI Server on port 8000...")
    try:
        # Using subprocess.run to keep it running in the foreground
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            env=env,
            cwd=os.getcwd()
        )
    except KeyboardInterrupt:
        print("\n🛑 Backend Server stopped.")

if __name__ == "__main__":
    start_backend()
