#!/usr/bin/env python3
"""
Disable inactive Port users.

What it does:
- Fetches users via GET /v1/users
- Filters users whose lastLoginAt is older than N days (or missing)
- Bulk-upserts status=Disabled on the _user blueprint via POST /v1/blueprints/_user/entities/bulk 

Prerequisites:
- Python 3.9+
- Optional but recommended: create a venv
    python -m venv .venv
    source .venv/bin/activate
- Install deps:
    pip install requests python-dotenv

Configuration (any of these: exported env vars, CLI flags, or .env if python-dotenv is installed):
- PORT_CLIENT_ID (required)
- PORT_CLIENT_SECRET (required)
- PORT_BASE_URL (default https://api.port.io)
- DAYS_INACTIVE (default 45)
- PORT_ORG_ID (optional; choose orgMembers entry)

Usage examples:
- Dry-run (no changes):
    python disable_inactive_users.py --dry-run
- Apply changes:
    python disable_inactive_users.py
- Override threshold / org:
    python disable_inactive_users.py --days-inactive 60 --org-id <ORG_ID>

Requirements:
- Client credentials must allow reading users and updating the _user blueprint.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from typing import Any, Dict, Iterable, List, Optional

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def parse_args() -> argparse.Namespace:
    if load_dotenv:
        load_dotenv()
    parser = argparse.ArgumentParser(
        description="Disable Port users inactive for more than N days.",
        epilog=(
            "Examples:\n"
            "  python scripts/disable_inactive_users.py --dry-run\n"
            "  python scripts/disable_inactive_users.py --days-inactive 60 --org-id <ORG_ID>"
        ),
    )
    parser.add_argument(
        "--client-id",
        default=os.getenv("PORT_CLIENT_ID"),
        help="Port client ID (env: PORT_CLIENT_ID)",
    )
    parser.add_argument(
        "--client-secret",
        default=os.getenv("PORT_CLIENT_SECRET"),
        help="Port client secret (env: PORT_CLIENT_SECRET)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("PORT_BASE_URL", "https://api.port.io"),
        help="Port API base URL (env: PORT_BASE_URL). Default: https://api.port.io",
    )
    parser.add_argument(
        "--days-inactive",
        type=int,
        default=int(os.getenv("DAYS_INACTIVE", "45")),
        help="Number of days since last login to consider inactive (env: DAYS_INACTIVE).",
    )
    parser.add_argument(
        "--org-id",
        default=os.getenv("PORT_ORG_ID"),
        help="Optional org ID to match in orgMembers; otherwise first/most recent is used.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Max users per bulk request (Port limit is 20).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call bulk API; only list users that would be disabled.",
    )
    return parser.parse_args()


def require(value: Optional[str], name: str) -> str:
    if value:
        return value
    print(f"Missing required credential: {name}", file=sys.stderr)
    sys.exit(1)


def get_token(session: requests.Session, base_url: str, client_id: str, client_secret: str) -> str:
    # Prefer /v1/auth/access_token; fall back to /auth/access_token for older deployments.
    url = base_url.rstrip("/")
    auth_url = f"{url}/v1/auth/access_token"
    resp = session.post(auth_url, json={"clientId": client_id, "clientSecret": client_secret}, timeout=30)
    if resp.status_code == 404:
        auth_url = f"{url}/auth/access_token"
        resp = session.post(auth_url, json={"clientId": client_id, "clientSecret": client_secret}, timeout=30)
    if resp.status_code != 200:
        print(f"Failed to get token ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    token = resp.json().get("accessToken")
    if not token:
        print("Token response missing accessToken", file=sys.stderr)
        sys.exit(1)
    return token


def fetch_users(session: requests.Session, base_url: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    url = base_url.rstrip("/") + "/v1/users"
    resp = session.get(url, headers=headers, timeout=60)
    if resp.status_code != 200:
        print(f"Failed to fetch users ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    data = resp.json()
    users = data.get("users") or data.get("data") or data
    if not isinstance(users, list):
        print("Unexpected users payload", file=sys.stderr)
        sys.exit(1)
    return users


def parse_ts(ts: Optional[str]) -> Optional[dt.datetime]:
    if not ts:
        return None
    try:
        # fromisoformat handles offset; ensure timezone-aware
        parsed = dt.datetime.fromisoformat(ts)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed
    except ValueError:
        return None


def select_last_login(user: Dict[str, Any], org_id: Optional[str]) -> Optional[dt.datetime]:
    entries = user.get("orgMembers") or []
    candidates: List[dt.datetime] = []
    for entry in entries:
        if org_id and entry.get("orgId") != org_id:
            continue
        parsed = parse_ts(entry.get("lastLoginAt"))
        if parsed:
            candidates.append(parsed)
    if not candidates and not org_id:
        # fallback to any lastLoginAt regardless of org_id
        for entry in entries:
            parsed = parse_ts(entry.get("lastLoginAt"))
            if parsed:
                candidates.append(parsed)
    return max(candidates) if candidates else None


def filter_inactive_users(
    users: Iterable[Dict[str, Any]],
    org_id: Optional[str],
    days_inactive: int,
) -> List[Dict[str, Any]]:
    now = dt.datetime.now(dt.timezone.utc)
    threshold = now - dt.timedelta(days=days_inactive)
    inactive: List[Dict[str, Any]] = []
    for user in users:
        if (user.get("status") or "").lower() == "disabled":
            continue
        last_login = select_last_login(user, org_id)
        if last_login is None or last_login <= threshold:
            inactive.append(
                {
                    "id": user.get("id") or user.get("email"),
                    "email": user.get("email"),
                    "last_login": last_login,
                }
            )
    return [u for u in inactive if u["id"]]


def chunked(seq: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def disable_batch(
    session: requests.Session,
    base_url: str,
    headers: Dict[str, str],
    batch: List[Dict[str, Any]],
) -> None:
    url = base_url.rstrip("/") + "/v1/blueprints/_user/entities/bulk"
    payload = {
        "entities": [
            {
                "identifier": user["id"],
                "title": user.get("email") or user["id"],
                "properties": {"status": "Disabled"},
                "upsert": True,
            }
            for user in batch
        ]
    }
    resp = session.post(url, json=payload, headers=headers, timeout=60)
    if resp.status_code not in (200, 207):
        print(f"Bulk disable failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    if resp.status_code == 207:
        print(f"Partial success (207): {resp.text}", file=sys.stderr)


def main() -> None:
    args = parse_args()
    client_id = require(args.client_id, "PORT_CLIENT_ID or --client-id")
    client_secret = require(args.client_secret, "PORT_CLIENT_SECRET or --client-secret")
    session = requests.Session()

    token = get_token(session, args.base_url, client_id, client_secret)
    headers = {"Authorization": f"Bearer {token}"}

    users = fetch_users(session, args.base_url, headers)
    inactive_users = filter_inactive_users(users, args.org_id, args.days_inactive)

    print(f"Found {len(users)} users; {len(inactive_users)} inactive (>{args.days_inactive} days).")
    if not inactive_users:
        return

    sample = inactive_users[:5]
    print("Sample inactive users:")
    for user in sample:
        last_login = user["last_login"].isoformat() if user["last_login"] else "none"
        print(f"- {user['id']} ({user.get('email') or 'no email'}), last_login={last_login}")
    if len(inactive_users) > len(sample):
        print(f"...and {len(inactive_users) - len(sample)} more.")

    if args.dry_run:
        print("Dry-run enabled; no users were disabled.")
        return

    for batch in chunked(inactive_users, args.batch_size):
        print(f"Disabling batch of {len(batch)} users...")
        disable_batch(session, args.base_url, headers, batch)
    print("Completed disabling inactive users.")


if __name__ == "__main__":
    main()

