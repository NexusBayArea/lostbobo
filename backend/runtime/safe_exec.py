import subprocess

def run_subprocess(cmd: list[str]):
    return subprocess.run(cmd, capture_output=True, text=True)
