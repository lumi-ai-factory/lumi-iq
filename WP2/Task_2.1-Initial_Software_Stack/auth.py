#!/usr/bin/env python3
"""
LUMI-IQ LEXIS Authentication Utility (OAuth 2.0 Device Code Flow):

Obtains a fresh LEXIS token via interactive browser login and saves it
securely to ~/.lumi-iq/token (permissions: 0600).
"""

import os
import sys
import time
import datetime
import argparse
import jwt
from config import LEXIS_PROJECT

TOKEN_DIR = os.path.expanduser("~/.lumi-iq")
TOKEN_FILE = os.path.join(TOKEN_DIR, "token")


def main():
    parser = argparse.ArgumentParser(
        description="LUMI-IQ LEXIS Re-authentication (OAuth 2.0 Device Code Flow)"
    )
    parser.add_argument(
        "--project",
        default=LEXIS_PROJECT,
        help=f"LEXIS project short name (default: {LEXIS_PROJECT})",
    )
    args = parser.parse_args()

    print(f"\n=== LEXIS Authentication (OAuth 2.0 Device Code Flow) ===")
    print(f"LEXIS Project: {args.project}")
    from qaas.client import QProvider

    provider = QProvider(lexis_project=args.project)
    token = provider._token

    if not token:
        print("ERROR: Authentication failed to obtain token.")
        sys.exit(1)

    os.makedirs(TOKEN_DIR, mode=0o700, exist_ok=True)
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with open(fd, "w") as f:
        f.write(token.strip())
    os.chmod(TOKEN_FILE, 0o600)

    payload = jwt.decode(token, options={"verify_signature": False})
    exp = payload.get("exp", 0)
    rem = exp - int(time.time())
    exp_dt = datetime.datetime.fromtimestamp(exp)

    print("\n" + "=" * 50)
    print("LEXIS AUTHENTICATION SUCCESSFUL")
    print("=" * 50)
    print(f"Token Saved To : {TOKEN_FILE} (chmod 0600)")
    print(f"Expires At     : {exp_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Valid For      : {rem}s ({rem // 60}m {rem % 60}s)")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
