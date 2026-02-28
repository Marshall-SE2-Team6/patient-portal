# Contributing Guide (Patient Portal)

This project uses a simple, team-friendly Git workflow:

**branch -> commits -> push -> PR -> merge -> sync main -> delete branch**

The goal is to keep `main` as the **latest known-good shared baseline** and keep feature branches small and short-lived.

---

## The 3 Git things you are always dealing with

- **Commits**: saved snapshots of the repo at a point in time.
- **Branches**: named pointers to commits (e.g., `main`, `feature/login`).
- **Remotes (GitHub)**: `origin` is the GitHub repo. GitHub stores copies like `origin/main`, `origin/feature/login`.

Local branches and GitHub branches line up when you **pull** (download) and **push** (upload).

---

## Daily workflow (standard loop)

### A) Start from a clean, up-to-date main
From the project root:

    git checkout main
    git pull origin main

### B) Create a branch for your task
Use a short, descriptive name:

    git checkout -b feature/<short-description>

Examples:
- `feature/dashboard-links`
- `fix/login-redirect`
- `chore/readme-update`

### C) Make only the relevant changes
Keep branches focused: one feature/fix per PR.

### D) Run checks locally before committing
From the project root (adjust if your structure differs):

    python manage.py check
    python manage.py migrate
    python manage.py runserver

Optional (if you changed models):

    python manage.py makemigrations
    python manage.py migrate

### E) Commit + push
    git status
    git add -A
    git commit -m "Short, specific message"
    git push -u origin feature/<short-description>

After the first push, GitHub will show a banner to open a PR.

### F) Open a PR -> merge into main
- Title your PR clearly and describe what changed.
- Request review if your team is doing reviews.
- Merge when approved (or when required checks pass).

### After merge (cleanup)
    git checkout main
    git pull origin main
    git branch -d feature/<short-description>

Optional (if GitHub does not auto-delete the remote branch):

    git push origin --delete feature/<short-description>

---

## Rules that prevent branching spaghetti

- Keep branches small (one task / one feature / one fix)
- Merge often (PRs should not sit forever)
- Sync your branch with `main` if it moves while you work
- Delete branches after merging
- Prefer PRs over direct pushes to `main`

---

## Syncing your branch when main changes

Simple and team-friendly approach: merge `origin/main` into your branch.

    git checkout feature/<short-description>
    git fetch origin
    git merge origin/main

If conflicts happen:
1) Resolve conflicts in files
2) Then:

    git add -A
    git commit
    git push

---

## Django-specific contribution rules

### Migrations
If you change `models.py`, include the generated migrations in the same PR:

    python manage.py makemigrations
    python manage.py migrate

Then commit the migration files.

### Do not commit local secrets or machine-specific files
Never commit:
- `.env`
- `.venv/`
- `__pycache__/`
- local database dumps / Docker volumes

---

## Essential commands (and what they tell you)

**Repo state (#1 command):**

    git status

Shows:
- current branch
- changed files
- staged vs unstaged
- whether you are ahead/behind `origin/<branch>`

**See branches:**

    git branch

**See recent history:**

    git log --oneline --graph --decorate -n 20

**Diffs:**

    git diff
    git diff --staged

---

## Undo / recovery (you will need these eventually)

**Unstage something (keep file changes):**

    git restore --staged <file>

**Discard local changes to a file (danger: loses edits):**

    git restore <file>

**Fix the last commit message (only if not pushed):**

    git commit --amend

**Stash work (save changes temporarily):**

    git stash
    git checkout main
    # later:
    git stash pop

---

## What a PR is (in practice)

A PR (Pull Request) is a GitHub workflow object that says:

"I have changes on this branch. Please merge them into that branch (usually `main`)."

PRs:
- show the exact file changes (diff)
- allow review and comments
- run checks/tests (if configured)
- provide a safe merge into `main`
