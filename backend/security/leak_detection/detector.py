import re


class LeakageDetector:
    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "api_key": r"(sk-|AKIA|Bearer\s)[A-Za-z0-9]{20,}",
        "secret": r"(password|key|token|secret)[:=]\s*[\"']?[A-Za-z0-9@\-_]{12,}",
    }

    async def scan(self, text: str) -> list[tuple[str, str]]:
        findings = []
        for name, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                findings.append((name, match.group(0)[:60] + "..."))
        return findings
