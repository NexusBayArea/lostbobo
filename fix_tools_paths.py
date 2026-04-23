import re
from pathlib import Path

ROOT = Path(".").resolve()

# directories to scan
SCAN_DIRS = ["backend", "tools"]  # include root tools just in case leftovers exist

# patterns to fix
IMPORT_PATTERNS = [
    (r"\bfrom tools\.", "from backend.tools."),
    (r"\bimport tools\.", "import backend.tools."),
]

PATH_PATTERNS = [
    (r'["\']tools/', '"backend/tools/'),
]

def fix_file(path: Path):
    text = path.read_text(encoding="utf-8")
    original = text

    # fix imports
    for pattern, replacement in IMPORT_PATTERNS:
        text = re.sub(pattern, replacement, text)

    # fix string paths
    for pattern, replacement in PATH_PATTERNS:
        text = re.sub(pattern, replacement, text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"[FIXED] {path}")


def scan():
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue

        for file in base.rglob("*.py"):
            fix_file(file)


def verify_no_root_tools_refs():
    print("\n[VERIFY] Checking for bad references...\n")

    bad = []
    for file in ROOT.rglob("*.py"):
        text = file.read_text(encoding="utf-8")

        if "from tools." in text or "import tools." in text:
            bad.append(file)

        if '"tools/' in text or "'tools/" in text:
            bad.append(file)

    if bad:
        print("❌ Remaining bad references:")
        for b in bad:
            print(b)
    else:
        print("✅ All references fixed")


if __name__ == "__main__":
    scan()
    verify_no_root_tools_refs()
