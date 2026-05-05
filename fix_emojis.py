import os

directory = "c:/Users/arche/SimHPC/backend/tools/ci_gates"
count = 0

# Replace common emojis with text markers
REPLACEMENTS = {
    "✅": "[OK]",
    "❌": "[FAIL]",
    "🚀": "[START]",
    "🌀": "[INIT]",
    "💾": "[SAVE]",
    "📈": "[SCALE]",
    "🔄": "[AUTO]",
    "💀": "[DEAD]",
    "🔧": "[FIX]",
    "⚠️": "[WARN]",
    "👋": "[EXIT]",
}

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                new_content = content
                for emoji, text in REPLACEMENTS.items():
                    new_content = new_content.replace(emoji, text)

                if new_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    count += 1
                    print(f"Fixed emojis in {filepath}")
            except Exception as e:
                print(f"Error on {filepath}: {e}")

print(f"Total files fixed: {count}")
