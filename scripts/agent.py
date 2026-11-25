#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyjwt[crypto]==2.10.1"]
# ///
"""Act on GitHub as the agent's App (`forja-agent`), never with the owner's own login.

    uv run scripts/agent.py push                 # push the current branch of this repository
    uv run scripts/agent.py run -- gh pr create --fill ...
    uv run scripts/agent.py run -- gh issue create ...

The App's key is read from its SOPS-encrypted file (FORJA_AGENT_SECRETS, by default the
`forja` repository's infra/github/secrets/forja-agent.env) and a short-lived installation
token is minted for the owner of the current repository. The token only lives in the
environment of the command it runs; it is never printed or written.
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import jwt

SECRETS = Path(os.environ.get("FORJA_AGENT_SECRETS",
                              Path.home() / "workspace/forja/infra/github/secrets/forja-agent.env"))
API = "https://api.github.com"


def app_credentials() -> tuple[str, str]:
    out = subprocess.run(["sops", "decrypt", "--input-type", "dotenv", "--output-type", "dotenv", str(SECRETS)],
                         capture_output=True, text=True, check=True).stdout
    env = dict(line.split("=", 1) for line in out.splitlines() if "=" in line and not line.startswith("sops_"))
    return env["GITHUB_APP_ID"], base64.b64decode(env["GITHUB_APP_PRIVATE_KEY_B64"]).decode()


def call(url: str, token: str, method: str = "GET") -> dict | list:
    req = urllib.request.Request(url, method=method, headers={"Authorization": f"Bearer {token}",
                                                             "Accept": "application/vnd.github+json",
                                                             "User-Agent": "forja-agent"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def repository() -> tuple[str, str]:
    url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True).stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+)/(.+?)(?:\.git)?$", url)
    if not m:
        sys.exit(f"origin is not a GitHub repository: {url}")
    return m[1], m[2]


def installation_token(owner: str) -> str:
    app_id, key = app_credentials()
    now = int(time.time())
    app_jwt = jwt.encode({"iat": now - 60, "exp": now + 540, "iss": app_id}, key, algorithm="RS256")
    inst = next((i for i in call(f"{API}/app/installations", app_jwt) if i["account"]["login"].lower() == owner.lower()), None)
    if inst is None:
        sys.exit(f"forja-agent is not installed on {owner}")
    return call(f"{API}/app/installations/{inst['id']}/access_tokens", app_jwt, "POST")["token"]


def run(cmd: list[str], token: str) -> int:
    with tempfile.TemporaryDirectory() as d:
        askpass = Path(d) / "askpass.sh"
        askpass.write_text('#!/bin/sh\ncase "$1" in Username*) echo x-access-token ;; *) echo "$AGENT_TOKEN" ;; esac\n')
        askpass.chmod(0o700)
        env = os.environ | {"GH_TOKEN": token, "AGENT_TOKEN": token, "GIT_ASKPASS": str(askpass),
                            "GIT_TERMINAL_PROMPT": "0"}
        return subprocess.run(cmd, env=env).returncode


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("push", "run"):
        sys.exit(__doc__)
    owner, name = repository()
    token = installation_token(owner)
    if sys.argv[1] == "push":
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True,
                                check=True).stdout.strip()
        if branch in ("main", "master"):
            sys.exit("the agent never pushes the default branch")
        return run(["git", "push", "--set-upstream", f"https://github.com/{owner}/{name}.git", f"HEAD:{branch}",
                    *sys.argv[2:]], token)
    cmd = sys.argv[3:] if sys.argv[2:3] == ["--"] else sys.argv[2:]
    return run(cmd, token)


if __name__ == "__main__":
    sys.exit(main())
