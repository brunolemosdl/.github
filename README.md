# .github

The engineering standard shared by the repositories of `brunolemosdl` and `tenebris-forge`:

| File | What |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | The standard: issues, branches, commits, pull requests, review, tags |
| [`pull_request_template.md`](pull_request_template.md), [`ISSUE_TEMPLATE/`](ISSUE_TEMPLATE) | Default templates for every repository without its own |
| [`.github/workflows/policy.yml`](.github/workflows/policy.yml) | Reusable check of a pull request against the standard |
| [`labels.json`](labels.json), [`repos.json`](repos.json) | Labels every repository gets, and the repositories in scope |
| [`scripts/apply.py`](scripts/apply.py) | Applies merge settings, labels and the branch ruleset to a repository |
| [`brand/`](brand) | The house style of the brand marks, the shared drawing kit and the pinned logo method |

A repository joins the standard with a `CODEOWNERS`, a short `REVIEW.md`, the caller
workflow below, and `python3 scripts/apply.py <owner>/<repo> --apply`.

```yaml
# .github/workflows/standard.yml
name: standard
on:
  pull_request:
    types: [opened, edited, synchronize, reopened]
permissions:
  contents: read
jobs:
  policy:
    uses: brunolemosdl/.github/.github/workflows/policy.yml@main
```
