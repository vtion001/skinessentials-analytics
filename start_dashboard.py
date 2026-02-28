#!/usr/bin/env python3
"""
Simple test to verify Streamlit is working
"""

import subprocess
import time
import sys


def start_streamlit():
    """Start Streamlit server"""
    cmd = [
        "streamlit",
        "run",
        "simple_dashboard.py",
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.runOnSave=false",
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/Users/archerterminez/agents/data-analyst",
        )

        # Wait a bit for it to start
        time.sleep(5)

        # Check if process is running
        if process.poll() is None:
            print("✅ Streamlit process is running")
            return process
        else:
            print("❌ Streamlit process terminated")
            return None

    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        return None


if __name__ == "__main__":
    process = start_streamlit()
    if process:
        print("🎉 Streamlit dashboard should be running on http://localhost:8501")
        print("Press Ctrl+C to stop the server")
        try:
            # Keep the script running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping Streamlit server...")
            process.terminate()
    else:
        print("❌ Failed to start Streamlit")
        sys.exit(1)
