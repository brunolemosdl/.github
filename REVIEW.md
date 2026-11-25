# Review

What failure looks like here: a rule in `CONTRIBUTING.md` that the check does not enforce
or enforces differently; a check that blocks a valid pull request (false positive is
worse than a missed nit); `apply.py` changing a repository it was not asked to, or
locking one with a required check that cannot run; a third-party action not pinned by
commit hash; any secret or personal data in this public repository.
