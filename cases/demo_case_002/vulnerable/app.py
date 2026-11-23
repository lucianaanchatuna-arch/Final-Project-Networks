import subprocess

def list_directory(directory):
    return subprocess.check_output(f"ls {directory}", shell=True, text=True)
