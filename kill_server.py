import os
import signal
import subprocess
import re

def kill_port_process(port):
    try:
        # Run netstat to find the process
        output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
        lines = output.strip().split('\n')
        for line in lines:
            if f":{port}" in line and "LISTENING" in line:
                parts = re.split(r'\s+', line.strip())
                pid = parts[-1]
                print(f"Found process {pid} on port {port}. Killing it...")
                os.system(f"taskkill /F /PID {pid}")
                return
        print(f"No process found on port {port}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    kill_port_process(8000)
