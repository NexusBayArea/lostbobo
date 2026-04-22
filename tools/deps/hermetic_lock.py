import hashlib
import subprocess
import sys
from pathlib import Path

LOCK_FILE = Path("requirements.lock")
HASH_FILE = Path(".requirements.lock.hash")
TMP_FILE = Path(".requirements.lock.tmp")


def run_compile():
    result = subprocess.run(
        [
            "uv",
            "pip",
            "compile",
            "pyproject.toml",
            "-o",
            str(TMP_FILE),
            "--no-header",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)


def normalize(text: str) -> str:
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(sorted(lines))


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def read(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def verify():
    run_compile()

    current = normalize(read(LOCK_FILE))
    generated = normalize(read(TMP_FILE))

    current_hash = hash_text(current)
    generated_hash = hash_text(generated)

    stored_hash = HASH_FILE.read_text().strip() if HASH_FILE.exists() else ""

    if current_hash != generated_hash:
        print("[FATAL] dependency lock content drift detected")
        print("Run: python tools/deps/hermetic_lock.py --write")
        sys.exit(1)

    if stored_hash and stored_hash != current_hash:
        print("[FATAL] dependency lock hash drift detected")
        sys.exit(1)

    print("[OK] hermetic dependency kernel stable")


def write():
    run_compile()

    normalized = normalize(read(TMP_FILE))
    LOCK_FILE.write_text(normalized)

    lock_hash = hash_text(normalized)
    HASH_FILE.write_text(lock_hash)

    print("[OK] lock updated + sealed")


if __name__ == "__main__":
    if "--write" in sys.argv:
        write()
    else:
        verify()
