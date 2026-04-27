#!/bin/sh

HOOK_PATH=".git/hooks/pre-commit"

echo "Installing pre-commit hook..."

cat > $HOOK_PATH << 'EOF'
#!/bin/sh
set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT/backend" || exit 0

python -m pip install ruff==0.4.4 >/dev/null 2>&1

FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -z "$FILES" ]; then
  exit 0
fi

python -m ruff format $FILES
python -m ruff check $FILES --fix

echo "$FILES" | xargs git add
EOF

chmod +x $HOOK_PATH

echo "Pre-commit hook installed."
