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

# LUMI HPC Slurm Project Account (e.g. project_462001789)
LUMI_PROJECT = os.getenv("LUMI_PROJECT", "project_462001789")

# LEXIS Platform Project Short Name (e.g. vlq_demo_project)
LEXIS_PROJECT = os.getenv("LEXIS_PROJECT", "vlq_demo_project")

# LEXIS Accounting Resource / QPU Backend (e.g. VLQ-CZ)
LEXIS_RESOURCE = os.getenv("LEXIS_RESOURCE", "VLQ-CZ")


def get_lexis_token() -> str | None:
    """Retrieves saved LEXIS OAuth token from env or ~/.lumi-iq/token."""
    token = os.getenv("LEXIS_TOKEN")
    if token:
        return token
    token_file = os.path.expanduser("~/.lumi-iq/token")
    if os.path.exists(token_file):
        try:
            with open(token_file, "r") as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass
    return None

