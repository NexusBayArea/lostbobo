#!/usr/bin/env python3
"""
SimHPC Magic Link Generator CLI

Generates demo access links for alpha pilots.
Can use the running API or create tokens directly via Supabase/Redis.

Usage:
  # Via API (requires running backend):
  python generate_demo_link.py --email pilot@coreshell.com --runs 5

  # Direct mode (standalone, uses Redis/Supabase directly):
  python generate_demo_link.py --email pilot@coreshell.com --runs 6 --direct

  # Customize expiry:
  python generate_demo_link.py --email pilot@coreshell.com --runs 5 --days 14
"""

import argparse
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timezone, timedelta


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_via_api(email: str, runs: int, days: int, api_url: str, api_key: str):
    """Generate demo link via the running API."""
    import urllib.request

    url = f"{api_url}/api/v1/demo/create"
    payload = json.dumps(
        {
            "email": email,
            "usage_limit": runs,
            "expiry_days": days,
        }
    ).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data
    except Exception as e:
        print(f"❌ API request failed: {e}")
        print("   Make sure the backend is running, or use --direct mode.")
        sys.exit(1)


def generate_direct(email: str, runs: int, days: int):
    """Generate demo link directly via Redis (no API needed)."""
    try:
        import redis
    except ImportError:
        print("❌ redis package required. Install: pip install redis")
        sys.exit(1)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()
    except Exception as e:
        print(f"❌ Redis connection failed ({redis_url}): {e}")
        sys.exit(1)

    token = secrets.token_hex(32)
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)

    demo_data = {
        "email": email,
        "token_hash": token_hash,
        "usage_limit": runs,
        "usage_count": 0,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    r.setex(
        f"demo:{token_hash}",
        days * 86400,
        json.dumps(demo_data),
    )

    # Also try Supabase if configured
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_url and supabase_key:
        try:
            from supabase import create_client

            client = create_client(supabase_url, supabase_key)
            client.table("demo_access").insert(demo_data).execute()
            print("  ✅ Also stored in Supabase demo_access table")
        except Exception as e:
            print(f"  ⚠️  Supabase insert skipped: {e}")

    return {
        "link": f"https://simhpc.com/demo/{token}",
        "token": token,
        "email": email,
        "usage_limit": runs,
        "expires_at": expires_at.isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate SimHPC magic demo links for alpha pilots"
    )
    parser.add_argument("--email", required=True, help="Pilot email address")
    parser.add_argument(
        "--runs", type=int, default=5, help="Number of simulation runs (default: 5)"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Link expiry in days (default: 7)"
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Generate directly via Redis (no API needed)",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("SIMHPC_API_URL", ""),
        help="Backend API URL (e.g. https://simhpc.com)",
    )
    parser.add_argument(
        "--api-key", default=os.getenv("SIMHPC_API_KEY", ""), help="Admin API key"
    )

    args = parser.parse_args()

    if not args.direct and not args.api_url:
        print("❌ --api-url required for API mode (or set SIMHPC_API_URL env var)")
        sys.exit(1)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🔗 SimHPC Magic Link Generator")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    if args.direct:
        print("  Mode:   Direct (Redis + Supabase)")
        result = generate_direct(args.email, args.runs, args.days)
    else:
        if not args.api_key:
            print("❌ --api-key required for API mode (or set SIMHPC_API_KEY env var)")
            print("   Alternatively, use --direct mode for local generation.")
            sys.exit(1)
        print(f"  Mode:   API ({args.api_url})")
        result = generate_via_api(
            args.email, args.runs, args.days, args.api_url, args.api_key
        )

    print(f"  Email:  {result['email']}")
    print(f"  Runs:   {result['usage_limit']}")
    print(f"  Expiry: {result['expires_at']}")
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("  ⚠️  SECURITY NOTICE: The link below contains a sensitive access token.")
    print(
        "  Do not share this link in public logs, CI/CD output, or insecure channels."
    )
    print()
    print("  🚀 Magic Link:")
    print()
    print(f"     {result['link']}")
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("  Send this link directly to your pilot.")
    print("  They click → auto-login → 5 simulations → demo ends.")
    print()


if __name__ == "__main__":
    main()
