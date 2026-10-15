#!/usr/bin/env python3
"""
LUMI-IQ LEXIS Authentication & Token Refresh Utility:

1. Checks for an existing token in ~/.lumi-iq/token and refresh token in ~/.lumi-iq/refresh_token.
2. If a valid refresh token exists:
   - Attempts non-interactive token renewal via Keycloak refresh token.
3. If no token exists, or refresh fails / refresh token expired:
   - Initiates interactive OAuth 2.0 Device Code Flow in the browser.
4. Securely stores tokens on disk:
   - ~/.lumi-iq/token (mode 0600)
   - ~/.lumi-iq/refresh_token (mode 0600)
5. Prints token expiration timestamp and remaining validity.
"""

import os
import sys
import time
import datetime
import argparse
import jwt

TOKEN_DIR = os.path.expanduser("~/.lumi-iq")
TOKEN_FILE = os.path.join(TOKEN_DIR, "token")
REFRESH_FILE = os.path.join(TOKEN_DIR, "refresh_token")
PROJECT = os.getenv("LEXIS_PROJECT", "vlq_demo_project")


def get_token_validity(token_str: str) -> tuple[int, int]:
    """Returns (exp_timestamp, remaining_seconds) from JWT exp claim."""
    try:
        payload = jwt.decode(token_str, options={"verify_signature": False})
        exp = payload.get("exp", 0)
        rem = exp - int(time.time())
        return exp, rem
    except Exception:
        return 0, 0


def save_secure_file(path: str, content: str):
    """Saves string content to file with strict 0600 permissions."""
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with open(fd, "w") as f:
        f.write(content.strip())
    os.chmod(path, 0o600)


def try_refresh_token() -> tuple[str | None, int, int]:
    """Attempts non-interactive token renewal via saved refresh token."""
    if not os.path.exists(REFRESH_FILE):
        return None, 0, 0
    try:
        with open(REFRESH_FILE, "r") as f:
            rf = f.read().strip()
        if not rf:
            return None, 0, 0
        from py4lexis.session import LexisSessionToken

        print("Attempting non-interactive renewal using saved refresh token...")
        session = LexisSessionToken(refresh_token=rf, suppress_print=True)
        new_access = session.get_access_token()
        new_rf = session.get_refresh_token()

        save_secure_file(TOKEN_FILE, new_access)
        if new_rf:
            save_secure_file(REFRESH_FILE, new_rf)

        exp, rem = get_token_validity(new_access)
        return new_access, exp, rem
    except Exception as e:
        print(f"Notice: Could not refresh using existing refresh token: {e}")
        return None, 0, 0


def authenticate_device_flow(project: str) -> tuple[str, int, int]:
    """Initiates interactive OAuth 2.0 Device Code Flow via QProvider/py4lexis."""
    print("\n=== Initiating LEXIS Authentication (OAuth 2.0 Device Code Flow) ===")
    from qaas.client import QProvider

    provider = QProvider(lexis_project=project)
    token = provider._token

    if not token:
        print("ERROR: Authentication failed to obtain token.")
        sys.exit(1)

    save_secure_file(TOKEN_FILE, token)
    print(f"Access token securely saved to {TOKEN_FILE} (permissions: 0600).")

    if hasattr(provider, "_session") and provider._session:
        try:
            rf = provider._session.get_refresh_token()
            if rf:
                save_secure_file(REFRESH_FILE, rf)
                print(f"Refresh token securely saved to {REFRESH_FILE} (permissions: 0600).")
        except Exception:
            pass

    exp, rem = get_token_validity(token)
    return token, exp, rem


def main():
    parser = argparse.ArgumentParser(
        description="LUMI-IQ LEXIS Authentication & Token Refresh Utility"
    )
    parser.add_argument(
        "--force-new",
        action="store_true",
        help="Force interactive browser login even if a refresh token exists",
    )
    parser.add_argument(
        "--project",
        default=PROJECT,
        help=f"LEXIS project short name (default: {PROJECT})",
    )
    args = parser.parse_args()

    token = None
    exp, rem = 0, 0

    if not args.force_new:
        # Check current token validity first
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, "r") as f:
                    candidate = f.read().strip()
                exp, rem = get_token_validity(candidate)
                if rem > 120:
                    print(f"Current token is still valid for {rem}s ({rem // 60}m {rem % 60}s).")
            except Exception:
                pass

        # Attempt refresh via refresh_token
        refreshed_token, exp, rem = try_refresh_token()
        if refreshed_token and rem > 60:
            token = refreshed_token
            print(f"[SUCCESS] Token refreshed non-interactively!")

    # If no valid token obtained via refresh, launch Device Code Flow
    if not token:
        if args.force_new:
            print("Force-new flag requested. Launching interactive authentication...")
        else:
            print("No valid token or refresh token available. Launching interactive authentication...")
        token, exp, rem = authenticate_device_flow(args.project)
        print(f"[SUCCESS] Interactive authentication completed!")

    exp_dt = datetime.datetime.fromtimestamp(exp)
    print("\n" + "=" * 50)
    print("TOKEN STATUS")
    print("=" * 50)
    print(f"Token File       : {TOKEN_FILE} (chmod 0600)")
    print(f"Refresh File     : {REFRESH_FILE} (chmod 0600)")
    print(f"Expires At       : {exp_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Remaining Time   : {rem}s ({rem // 60}m {rem % 60}s)")
    print("=" * 50)


if __name__ == "__main__":
    main()
