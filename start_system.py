import subprocess
import time
import sys
import os
import signal

def run_system():
    # Use environment copy to ensure paths are correct
    env = os.environ.copy()
    
    print("🚀 Starting FastAPI Server on port 8000...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        env=env,
        cwd=os.getcwd()
    )
    
    # Wait a bit for server to start
    time.sleep(3)
    
    print("🚀 Starting Streamlit App on port 8501...")
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "home.py"],
        env=env,
        cwd=os.getcwd()
    )
    
    print("✅ System running! Press Ctrl+C to stop.")
    
    try:
        # Keep main process alive
        while True:
            time.sleep(1)
            # Check if processes are alive
            if server_process.poll() is not None:
                print("❌ Server process exited unexpectedy.")
                break
            if streamlit_process.poll() is not None:
                print("❌ Streamlit process exited unexpectedy.")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
    finally:
        # Terminate processes
        if server_process.poll() is None:
            server_process.terminate()
            print("Terminated Server.")
        if streamlit_process.poll() is None:
            streamlit_process.terminate()
            print("Terminated Streamlit.")

if __name__ == "__main__":
    run_system()
