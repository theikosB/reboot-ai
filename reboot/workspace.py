
from pathlib import Path
import subprocess


def inspect_project(project_path: str) -> dict:
    """Collect a small, safe-to-display summary of a local Git project."""
    root = Path(project_path).expanduser().resolve()

    if not root.is_dir():
        raise ValueError("That folder does not exist.")

    if not (root / ".git").exists():
        raise ValueError("That folder is not a Git repository.")

    def git(*args):
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()

    readme = ""
    for name in ("README.md", "README.rst", "README.txt", "README"):
        file = root / name
        if file.is_file():
            readme = file.read_text(encoding="utf-8", errors="replace")[:5000]
            break

    files = git("ls-files")
    file_list = files.splitlines()[:100] if files else []

    commits = git("log", "-5", "--pretty=format:%h | %s")
    status = git("status", "--short")
    todo_lines = []

    for relative in file_list:
        if len(todo_lines) >= 30:
            break

        file_path = root / relative
        if not file_path.is_file() or file_path.suffix.lower() not in {
            ".py", ".md", ".txt", ".js", ".ts", ".html", ".css",
            ".java", ".cpp", ".h", ".tex", ".r", ".jl"
        }:
            continue

        try:
            lines = file_path.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
        except OSError:
            continue

        for number, line in enumerate(lines, start=1):
            if any(marker in line.upper() for marker in ("TODO", "FIXME", "XXX")):
                todo_lines.append(f"{relative}:{number}: {line.strip()[:180]}")
                if len(todo_lines) >= 30:
                    break

    return {
        "path": str(root),
        "readme": readme or "No README found.",
        "files": file_list,
        "commits": commits.splitlines() if commits else [],
        "status": status.splitlines() if status else [],
        "todos": todo_lines,
    }
