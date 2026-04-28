import subprocess


def run():
    r = subprocess.run(["python", "-m", "ruff", "format", "--check", "."])
    return r.returncode == 0
