"""
LUMI-IQ Centralized Configuration Loader

Loads project settings with priority:
  1. Active OS Environment Variables
  2. Local .env file in the task directory
  3. Global user config in ~/.lumi-iq/config
  4. Project defaults
"""

import os


def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    candidates = [
        os.path.join(script_dir, ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.expanduser("~/.lumi-iq/config"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            except Exception:
                pass


load_config()

# LUMI HPC Slurm Project Account (e.g. project_<id>)
LUMI_PROJECT = os.getenv("LUMI_PROJECT", "")

# LEXIS Platform Project Short Name (e.g. your_vlq_project)
LEXIS_PROJECT = os.getenv("LEXIS_PROJECT", "your_vlq_project")

# LEXIS Accounting Resource / QPU Backend (e.g. VLQ-CZ)
LEXIS_RESOURCE = os.getenv("LEXIS_RESOURCE", "VLQ-CZ")


def get_token_remaining_seconds(token_str: str) -> int:
    """Returns remaining lifetime in seconds from JWT exp claim, or 0 if invalid."""
    try:
        import time
        import jwt
        payload = jwt.decode(token_str, options={"verify_signature": False})
        exp = payload.get("exp", 0)
        return exp - int(time.time())
    except Exception:
        return 0


def get_lexis_token(min_remaining_sec: int = 60) -> str | None:
    """
    Retrieves saved LEXIS OAuth token from env or ~/.lumi-iq/token.
    Validates expiration. If missing, invalid, or remaining lifetime <= min_remaining_sec,
    returns None so that callers can trigger OAuth Device Flow automatically.
    """
    token = os.getenv("LEXIS_TOKEN")
    if token:
        rem = get_token_remaining_seconds(token)
        if rem > min_remaining_sec:
            return token
        else:
            print(f"[NOTICE] $LEXIS_TOKEN is expired or near expiry ({rem}s remaining).")

    token_file = os.path.expanduser("~/.lumi-iq/token")
    if os.path.exists(token_file):
        try:
            with open(token_file, "r") as f:
                content = f.read().strip()
                if content:
                    rem = get_token_remaining_seconds(content)
                    if rem > min_remaining_sec:
                        return content
                    else:
                        print(f"[NOTICE] Cached token in ~/.lumi-iq/token is expired or near expiry ({rem}s remaining).")
        except Exception:
            pass

    return None


def save_lexis_token(token_str: str, token_path: str = "~/.lumi-iq/token") -> None:
    """Persists token string to file with strict chmod 0600 permissions."""
    path = os.path.expanduser(token_path)
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with open(fd, "w") as f:
        f.write(token_str.strip())
    os.chmod(path, 0o600)
    print(f"Token saved securely to {path} (permissions: 0600).")


