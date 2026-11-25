# Engineering standard

How work is done in every repository of `brunolemosdl` and `tenebris-forge`. Agents
(`forja-agent[bot]`) and people follow the same rules. The checks in
[`policy.yml`](.github/workflows/policy.yml) enforce what can be enforced.

## Work starts from an issue

Every change has an issue in its repository. The issue number is the task id:
`TASK-123` in commits, `task-123` in branch names. Open issues with the forms of this
repository (feature, bug, chore); they ask for context, goal, acceptance criteria, the
area touched, risk and source.

| Label | Meaning |
|---|---|
| `status:proposed` | Found by the agent; waits for the owner to release it |
| `status:ready` | Released: may be taken |
| `status:in-progress` | Someone is on it |
| `status:in-review` | A pull request is open |
| `status:blocked` | Waits on something outside |
| `status:needs-owner` | Needs a decision from the owner |
| `priority:high`, `priority:normal`, `priority:low` | Order in the queue |
| `source:owner`, `source:agent` | Who asked for it |

An issue from the owner's own request is born `status:ready`; one an agent found is born
`status:proposed`.

## Branches

```
<type>/<task-id>/<scope>/<short-description>
feat/task-123/auth/password-reset
```

Lowercase, English, words joined by hyphens, task id required. One issue per branch.

## Commits

```
<type>(<scope>): [<task-id>] <short description>

<detailed description>
```

```
feat(auth): [TASK-123] add password reset functionality

- Implement password reset endpoint.
- Validate reset token expiration.
- Add unit tests for password reset flow.
```

- Conventional Commits with the scope required and the task id whenever there is an issue.
- The short description is English, imperative, lowercase, without a final period.
- A simple change is that one line. A complex one adds a blank line and one `- ` line per
  change made.
- The author is the owner. No co-author, no tool trailer, no trace of AI tooling.

| Type | For |
|---|---|
| `feat` | New functionality |
| `fix` | Bug fix |
| `refactor` | Code change that keeps behaviour |
| `docs` | Documentation |
| `style` | Formatting |
| `test` | Tests |
| `perf` | Performance |
| `build` | Build and dependencies |
| `ci` | Continuous integration and delivery |
| `chore` | General maintenance |
| `revert` | Reverting changes |

## Pull requests

The title is the commit header. The body follows the template and starts with
`Closes #<issue>`. Before opening it, the author runs the checks and a review of the diff
in a fresh context (correctness and security) and answers every finding; after three
rounds without converging, the author stops and asks the owner.

Pull requests merge by rebase, with auto-merge on, and the branch is deleted after.

## Review only where it matters

Each repository has a `CODEOWNERS` file naming the owner on its sensitive paths. A pull
request that touches none of them merges by itself when the checks pass; one that touches
any waits for the owner. A new push dismisses an earlier approval, and open threads block
the merge. Always owned: `.github/`, `CODEOWNERS`, `CLAUDE.md`, `REVIEW.md`, dependency
manifests and lock files, deploy and infrastructure files.

`REVIEW.md` in each repository says, in a few lines, what failure looks like there.

## Tags

A repository starts tagging only when its owner declares the first version done
(`v1.0.0`, annotated). From then on, semantic versions follow the merged commits.

## Exceptions

- Renovate's branches and commits (no issue behind them).
- Repositories with the `vault` profile in [`repos.json`](repos.json) have no issues and no
  pull requests; their commits follow the format above without a task id.
