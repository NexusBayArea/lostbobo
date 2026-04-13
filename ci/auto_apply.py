import subprocess
import os

THRESHOLD = 0.75

def maybe_apply(patch_cmd, confidence):
    """Applies a predicted fix if the confidence meets the threshold."""
    if not patch_cmd:
        return False
        
    if confidence < THRESHOLD:
        print(f"Confidence {confidence} below threshold {THRESHOLD}. Skipping auto-fix.")
        return False

    print(f"Applying predicted fix: {' '.join(patch_cmd)} (confidence={confidence})")

    try:
        result = subprocess.run(
            patch_cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print("Auto-fix applied successfully.")
            return True
        else:
            print(f"Auto-fix failed with exit code {result.returncode}:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"Execution error during auto-fix: {e}")
        return False
