"""Read local settings without shell evaluation or third-party dependencies."""

import getpass
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = {"CSES_USERNAME", "CSES_PASSWORD", "CSES_EDITOR"}


def read_dotenv(root):
    path = Path(root) / ".env"
    if not path.exists():
        return {}
    values = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if key not in KEYS:
            continue
        if not separator:
            raise ValueError(f"{path}:{number}: expected KEY=value")
        value = value.strip()
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f"{path}:{number}: unmatched quote")
            value = value[1:-1]
        # Values are literal: no interpolation, escape processing, or execution.
        values[key] = value
    return values


def get_credentials(username=None, password=None, root=ROOT):
    local = read_dotenv(root)
    username = username or os.environ.get("CSES_USERNAME") or local.get("CSES_USERNAME")
    if not username:
        username = input("CSES username: ").strip()
    if not username:
        raise ValueError("Username cannot be empty.")
    if password is None:
        password = os.environ.get("CSES_PASSWORD", local.get("CSES_PASSWORD"))
    if password is None or password == "":
        password = getpass.getpass("CSES password: ")
    return username, password
