import subprocess
from config import REPO_PATH


class GitError(Exception):
    """Raised when a git operation fails."""
    pass


def _run_git(*args: str) -> str:
    """Run a git command in the repo directory."""
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_PATH,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise GitError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def has_remote() -> bool:
    """Check if a remote is configured."""
    try:
        result = _run_git("remote")
        return bool(result.strip())
    except GitError:
        return False


def pull() -> None:
    """Pull latest changes with rebase. Skips if no remote configured."""
    if not has_remote():
        return  # No remote, nothing to pull

    try:
        _run_git("pull", "--rebase")
    except GitError as e:
        err = str(e).lower()
        # Skip pull errors for new repos with no tracking branch
        if "no tracking information" in err or "there is no tracking" in err:
            return
        if "conflict" in err:
            try:
                _run_git("rebase", "--abort")
            except GitError:
                pass
            raise GitError("Merge conflict detected. Please resolve manually.")
        raise


def commit_and_push(message: str) -> None:
    """Stage all server data and config, commit, and push."""
    _run_git("add", "servers/")
    _run_git("add", "config.json")

    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=REPO_PATH
    )
    if result.returncode == 0:
        # No changes staged
        return

    _run_git("commit", "-m", f"Bot: {message}")

    # Only push if remote is configured
    if not has_remote():
        return

    try:
        _run_git("push")
    except GitError as e:
        err = str(e).lower()
        if "rejected" in err or "failed to push" in err:
            raise GitError("Push rejected. Someone else may have pushed. Please try again.")
        if "no upstream branch" in err or "has no upstream" in err:
            return  # No upstream configured, skip push
        raise


def sync_and_commit(message: str) -> None:
    """Pull, then commit and push. Full sync operation."""
    pull()
    commit_and_push(message)
