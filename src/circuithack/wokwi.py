from __future__ import annotations

import os
import subprocess
import sys

from .env import auto_load_env


def main() -> None:
    # Load .env from current working directory (or nearest parent) first.
    auto_load_env()

    cli_bin = os.environ.get("WOKWI_CLI_BIN", "/Users/abossard/bin/wokwi-cli")
    cmd = [cli_bin, *sys.argv[1:]]
    completed = subprocess.run(cmd, check=False)
    raise SystemExit(completed.returncode)
