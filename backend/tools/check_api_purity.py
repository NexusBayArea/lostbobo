import sys

FORBIDDEN = ["numpy", "scipy", "torch"]

with open("backend/requirements.api.lock") as f:
    content = f.read()

violations = [pkg for pkg in FORBIDDEN if pkg in content]

if violations:
    print(f"API lock contaminated: {violations}")
    sys.exit(1)

print("API purity OK")
