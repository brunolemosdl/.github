#!/usr/bin/env python3
"""The engineering standard's check for a pull request (CONTRIBUTING.md).

Run by the reusable workflow `.github/workflows/policy.yml` inside the checked-out
repository, with the pull request event in GITHUB_EVENT_PATH. Prints every problem
found and exits 1 if there is any. Standard library only.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

TYPES = "feat|fix|refactor|docs|style|test|perf|build|ci|chore|revert"
BRANCH = re.compile(rf"^({TYPES})/task-(\d+)/[a-z0-9]+(-[a-z0-9]+)*/[a-z0-9]+(-[a-z0-9]+)*$")
HEADER = re.compile(rf"^({TYPES})\(([a-z0-9]+(?:[-./][a-z0-9]+)*)\)!?: \[TASK-(\d+)\] ([a-z0-9].*)$")
TRAILER = re.compile(r"^(co-authored-by|signed-off-by|generated-by|reviewed-by|assisted-by)\s*:", re.I)
# tool signatures, not mentions: a commit may well talk about Claude Code or Copilot
TOOLING = re.compile(r"(generated|written|created) (with|by) (claude|copilot|chatgpt|an? ai)|\U0001F916", re.I)
CLOSES = re.compile(r"\b(?:closes|fixes|resolves)\s+#(\d+)\b", re.I)
SECRETS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("AWS key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}")),
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
]
EXEMPT_BRANCHES = ("renovate/", "dependabot/")
EXEMPT_AUTHORS = ("renovate[bot]", "dependabot[bot]")
MAX_HEADER = 100


def check_header(text: str, where: str, task: str | None) -> list[str]:
    m = HEADER.match(text)
    if not m:
        return [f"{where}: '{text}' is not `<type>(<scope>): [TASK-n] <short description>`"]
    errs = []
    if task and m[3] != task:
        errs.append(f"{where}: task TASK-{m[3]} differs from the branch's task-{task}")
    if text.endswith("."):
        errs.append(f"{where}: no final period")
    if len(text) > MAX_HEADER:
        errs.append(f"{where}: header longer than {MAX_HEADER} characters")
    return errs


def check_message(sha: str, message: str, author: str, owner: str, task: str | None) -> list[str]:
    where = f"commit {sha[:7]}"
    lines = message.rstrip("\n").split("\n")
    errs = check_header(lines[0], where, task)
    if owner and author != owner:
        errs.append(f"{where}: author is '{author}', expected '{owner}'")
    if len(lines) > 1:
        if lines[1].strip():
            errs.append(f"{where}: a blank line must separate the header from the description")
        for ln in lines[2:]:
            if ln.strip() and not ln.startswith(("- ", "  ")):
                errs.append(f"{where}: description lines start with '- ' (got '{ln[:40]}')")
                break
    for ln in lines[1:]:
        if TRAILER.match(ln.strip()):
            errs.append(f"{where}: trailer '{ln.strip()}' is not allowed")
        elif TOOLING.search(ln):
            errs.append(f"{where}: no trace of AI tooling ('{ln.strip()[:40]}')")
    return errs


def check_added(diff: str) -> list[str]:
    errs, path = [], None
    for ln in diff.splitlines():
        if ln.startswith("+++ "):
            path = ln[6:] if ln.startswith("+++ b/") else None
            continue
        if not ln.startswith("+") or path is None:
            continue
        text = ln[1:]
        if path.endswith(".md") and "—" in text:
            errs.append(f"{path}: em dash in an added line ('{text.strip()[:50]}')")
        for name, pat in SECRETS:
            if pat.search(text):
                errs.append(f"{path}: looks like a {name} in an added line")
    return errs


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def main() -> int:
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"]))
    pr = event["pull_request"]
    owner = os.environ.get("OWNER_NAME", "")
    branch, title, body = pr["head"]["ref"], pr["title"], pr.get("body") or ""
    base, head = pr["base"]["sha"], pr["head"]["sha"]
    if branch.startswith(EXEMPT_BRANCHES) or pr["user"]["login"] in EXEMPT_AUTHORS:
        print(f"{branch}: exempt from the standard (dependency updates)")
        return 0
    errs: list[str] = []
    m = BRANCH.match(branch)
    task = m[2] if m else None
    if not m:
        errs.append(f"branch '{branch}' is not `<type>/task-<n>/<scope>/<short-description>`")
    errs += check_header(title, "title", task)
    closes = CLOSES.findall(body)
    if not closes:
        errs.append("body: start with `Closes #<issue>`")
    elif task and task not in closes:
        errs.append(f"body: closes #{', #'.join(closes)} but the branch is task-{task}")
    log = git("log", "--format=%H%x1f%an%x1f%B%x1e", f"{base}..{head}")
    for rec in filter(None, (r.strip("\n") for r in log.split("\x1e"))):
        sha, author, message = rec.split("\x1f", 2)
        errs += check_message(sha, message, author, owner, task)
    errs += check_added(git("diff", "--unified=0", f"{base}...{head}"))
    for e in errs:
        print(f"::error::{e}")
    print(f"{len(errs)} problem(s)" if errs else "the pull request follows the standard")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
