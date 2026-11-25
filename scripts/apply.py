#!/usr/bin/env python3
"""Apply the engineering standard to repositories: merge settings, labels and the ruleset
that protects the default branch. Runs with the owner's own `gh` login (admin), never
with the agent's App.

    python3 scripts/apply.py brunolemosdl/forja            # show what would change
    python3 scripts/apply.py brunolemosdl/forja --apply    # change it
    python3 scripts/apply.py --all [--apply]               # every repository in repos.json

The policy check becomes required only once the repository has the caller workflow
`.github/workflows/standard.yml`, so a repository is never locked by a check that
cannot run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULESET = "main"
CALLER = ".github/workflows/standard.yml"
POLICY_CHECK = "policy / check"
ADMIN_ROLE = 5  # repository role "admin": may merge a pull request without the rules, never push

SETTINGS = {"allow_squash_merge": False, "allow_merge_commit": False, "allow_rebase_merge": True,
            "allow_auto_merge": True, "delete_branch_on_merge": True, "allow_update_branch": True}


def gh(method: str, path: str, body: dict | None = None, ok404: bool = False):
    cmd = ["gh", "api", "-X", method, path, "-H", "Accept: application/vnd.github+json"]
    if body is not None:
        cmd += ["--input", "-"]
    r = subprocess.run(cmd, input=json.dumps(body) if body is not None else None, capture_output=True, text=True)
    if r.returncode != 0:
        if ok404 and "404" in (r.stdout + r.stderr):
            return None
        raise RuntimeError(f"{method} {path}: {(r.stdout or r.stderr).strip()[:300]}")
    return json.loads(r.stdout) if r.stdout.strip() else {}


def ruleset(profile: str, checks: list[str], owner_review: bool = True) -> dict:
    rules: list[dict] = [{"type": "deletion"}, {"type": "non_fast_forward"}]
    bypass: list[dict] = []
    if profile == "standard":
        rules += [
            {"type": "required_linear_history"},
            {"type": "pull_request", "parameters": {
                "required_approving_review_count": 0, "dismiss_stale_reviews_on_push": True,
                "require_code_owner_review": owner_review, "require_last_push_approval": False,
                "required_review_thread_resolution": True, "allowed_merge_methods": ["rebase"]}},
        ]
        if checks:
            rules.append({"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": False, "do_not_enforce_on_create": False,
                "required_status_checks": [{"context": c} for c in checks]}})
        bypass = [{"actor_id": ADMIN_ROLE, "actor_type": "RepositoryRole", "bypass_mode": "pull_request"}]
    return {"name": RULESET, "target": "branch", "enforcement": "active", "bypass_actors": bypass,
            "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}}, "rules": rules}


def apply(entry: dict, labels: list[dict], do: bool) -> list[str]:
    repo, profile = entry["repo"], entry["profile"]
    done: list[str] = []
    info = gh("GET", f"repos/{repo}")
    if profile == "standard":
        diff = {k: v for k, v in SETTINGS.items() if info.get(k) != v}
        if diff:
            done.append(f"settings {diff}")
            if do:
                gh("PATCH", f"repos/{repo}", diff)
        have = {lb["name"]: lb for lb in gh("GET", f"repos/{repo}/labels?per_page=100")}
        for lb in labels:
            cur = have.get(lb["name"])
            if cur is None:
                done.append(f"label + {lb['name']}")
                if do:
                    gh("POST", f"repos/{repo}/labels", lb)
            elif cur["color"].lower() != lb["color"].lower() or (cur.get("description") or "") != lb["description"]:
                done.append(f"label ~ {lb['name']}")
                if do:
                    gh("PATCH", f"repos/{repo}/labels/{lb['name'].replace(':', '%3A')}", lb)
    has_caller = gh("GET", f"repos/{repo}/contents/{CALLER}", ok404=True) is not None
    checks = ([POLICY_CHECK] if has_caller else []) + entry.get("checks", [])
    want = ruleset(profile, checks if has_caller else [], entry.get("owner_review", True))
    current = next((r for r in gh("GET", f"repos/{repo}/rulesets") if r["name"] == RULESET), None)
    if current is None:
        done.append(f"ruleset + {RULESET} ({profile}, checks: {want_checks(want) or 'none yet'})")
        if do:
            gh("POST", f"repos/{repo}/rulesets", want)
    else:
        full = gh("GET", f"repos/{repo}/rulesets/{current['id']}")
        if norm(full) != norm(want):
            done.append(f"ruleset ~ {RULESET} ({profile}, checks: {want_checks(want) or 'none yet'})")
            if do:
                gh("PUT", f"repos/{repo}/rulesets/{current['id']}", want)
    if profile == "standard" and not has_caller:
        done.append(f"note: no {CALLER} yet, so the policy check is not required")
    return done


def want_checks(rs: dict) -> list[str]:
    return [c["context"] for r in rs["rules"] if r["type"] == "required_status_checks"
            for c in r["parameters"]["required_status_checks"]]


def norm(rs: dict) -> str:
    rules = sorted(({"type": r["type"], "parameters": {k: v for k, v in (r.get("parameters") or {}).items()
                                                         if k in ("required_approving_review_count", "dismiss_stale_reviews_on_push",
                                                                  "require_code_owner_review", "required_review_thread_resolution",
                                                                  "allowed_merge_methods", "required_status_checks")}}
                    for r in rs.get("rules", [])), key=lambda r: r["type"])
    bypass = sorted((b["actor_id"], b["actor_type"], b["bypass_mode"]) for b in rs.get("bypass_actors") or [])
    return json.dumps({"rules": rules, "bypass": bypass, "enf": rs.get("enforcement")}, sort_keys=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    known = {e["repo"]: e for e in json.loads((ROOT / "repos.json").read_text())["repos"]}
    labels = json.loads((ROOT / "labels.json").read_text())
    names = list(known) if a.all else a.repos
    if not names:
        ap.error("name repositories or use --all")
    bad = 0
    for name in names:
        entry = known.get(name)
        if entry is None:
            print(f"{name}: not in repos.json")
            bad += 1
            continue
        try:
            changes = apply(entry, labels, a.apply)
        except RuntimeError as e:
            print(f"{name}: {e}")
            bad += 1
            continue
        verb = "applied" if a.apply else "would apply"
        print(f"{name}: " + ("up to date" if not changes else f"{verb}:\n  " + "\n  ".join(changes)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
