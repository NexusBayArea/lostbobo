import os

def check_context():
    repo_files = set()

    for root, _, files in os.walk("."):
        if ".git" in root or "node_modules" in root or "__pycache__" in root:
            continue
        for f in files:
            path = os.path.join(root, f).replace("\\", "/")
            if path.startswith("./"):
                path = path[2:]
            repo_files.add(path)

    docker_ignored = []
    if os.path.exists(".dockerignore"):
        with open(".dockerignore", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    docker_ignored.append(line)

    print("\n=== POTENTIAL MISSING DOCKER FILES ===")
    
    # Check essential files for Docker context
    essential_files = [
        "requirements.txt",
        "api.py",
        "worker.py",
        "app/main.py",
        "docker/images/Dockerfile.unified",
        "docker/supervisor/supervisord.conf"
    ]

    for f in essential_files:
        if not os.path.exists(f):
            print(f"❌ MISSING ESSENTIAL FILE: {f}")
        else:
            print(f"✅ FOUND: {f}")

    print("\n=== IGNORED BY .DOCKERIGNORE ===")
    for f in sorted(repo_files):
        # Basic matching for demo purposes
        for pattern in docker_ignored:
            if pattern.endswith("/") and pattern[:-1] in f:
                 print(f"⚠️ ignored: {f}")
                 break
            elif pattern in f:
                 print(f"⚠️ ignored: {f}")
                 break

if __name__ == "__main__":
    check_context()
