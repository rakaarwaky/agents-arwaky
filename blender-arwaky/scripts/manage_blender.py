import os
import socket
import subprocess
import time

BLENDER_PATH = "/home/raka/SharedData/App/Blender/blender"


def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def start_blender():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))

    script_path = os.path.join(current_dir, "run_headless.py")
    log_path = os.path.join(project_root, "log", "blender.log")

    # Kill existing
    subprocess.run(["pkill", "-x", "blender"], capture_output=True)
    time.sleep(1)

    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Set environment for stability + display
    env = os.environ.copy()
    env["DISPLAY"] = ":0"
    env["WAYLAND_DISPLAY"] = "wayland-1"

    print(f"Starting Blender with log: {log_path}")
    with open(log_path, "w") as log_file:
        process = subprocess.Popen(
            [BLENDER_PATH, "--background", "--python", script_path],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
            preexec_fn=os.setpgrp,  # detach
        )

    print(f"Started Blender (PID: {process.pid})")

    # Wait for port
    print("Waiting for port 9876...")
    for i in range(30):
        if is_port_open(9876):
            print("Port 9876 is OPEN!")
            return True
        time.sleep(1)
        if process.poll() is not None:
            print("Process died unexpectedly!")
            return False

    print("Timed out waiting for port.")
    return False


if __name__ == "__main__":
    start_blender()
