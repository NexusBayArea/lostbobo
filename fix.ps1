cd backend
uv run ruff format .
uv run ruff check . --fix --unsafe-fixes
git add .
git commit -m "fix: ruff + pre-commit cleanup" --allow-empty
git push
Write-Host "✅ Fix completed and pushed" -ForegroundColor Green
