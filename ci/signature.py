import re

def extract_signature(stderr: str) -> str:
    """Normalizes error logs into a stable signature by stripping variable data."""
    if not stderr:
        return "empty_stderr"
        
    lines = stderr.splitlines()

    # Look for the last line that looks like an error/exception
    for line in reversed(lines):
        if "Error" in line or "Exception" in line:
            # Replace numbers and paths with placeholders to normalize
            normalized = re.sub(r'\d+', '<num>', line.strip())
            # Replace file paths
            normalized = re.sub(r'["\']/[^"\']+["\']', '<path>', normalized)
            return normalized

    # Fallback to first 200 chars if no obvious error line found
    return stderr[:200].strip().replace("\n", " ")
