import subprocess
import sys
import os

def start_frontend():
    env = os.environ.copy()
    print("🚀 Starting Streamlit App on port 8501...")
    try:
        # Using subprocess.run to keep it running in the foreground
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "home.py"],
            env=env,
            cwd=os.getcwd()
        )
    except KeyboardInterrupt:
        print("\n🛑 Frontend App stopped.")

if __name__ == "__main__":
    start_frontend()
