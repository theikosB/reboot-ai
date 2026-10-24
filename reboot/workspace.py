
from pathlib import Path
import subprocess


SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".cpp", ".cc", ".c", ".h", ".hpp",
    ".rs", ".go", ".r", ".jl", ".tex",
}

TEXT_EXTENSIONS = SOURCE_EXTENSIONS | {
    ".md", ".txt", ".html", ".css", ".toml",
    ".yaml", ".yml", ".json",
}

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules",
    "__pycache__", "dist", "build", ".next",
    ".pytest_cache", ".mypy_cache", "coverage",
}

EXCLUDED_NAMES = {
    ".env", ".env.local", ".env.production",
    "id_rsa", "id_ed25519", "credentials.json",
    "secrets.json", "package-lock.json",
    "yarn.lock", "pnpm-lock.yaml",
}

MAX_FILE_BYTES = 100_000
MAX_SOURCE_FILES = 12
MAX_SOURCE_CHARS = 30_000


def inspect_project(project_path: str) -> dict:
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
            timeout=15,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    readme = ""
    for name in ("README.md", "README.rst", "README.txt", "README"):
        path = root / name
        if path.is_file():
            readme = path.read_text(
                encoding="utf-8", errors="replace"
            )[:6000]
            break

    # Includes tracked and untracked, non-ignored files.
    raw_files = git(
        "ls-files", "--cached", "--others",
        "--exclude-standard", "-z"
    )

    file_list = []
    for relative in raw_files.split("\0"):
        if not relative:
            continue

        path = Path(relative)

        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue

        if path.name in EXCLUDED_NAMES:
            continue

        if path.name.startswith(".env.") and path.name != ".env.example":
            continue

        full_path = root / path

        if full_path.is_symlink() or not full_path.is_file():
            continue

        if full_path.stat().st_size > MAX_FILE_BYTES:
            continue

        file_list.append(relative)

    file_list = sorted(set(file_list))[:150]

    commits = git("log", "-5", "--pretty=format:%h | %s")
    status = git("status", "--short")

    todos = []
    source_files = []
    total_source_chars = 0

    for relative in file_list:
        path = root / relative

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        try:
            content = path.read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            continue

        for number, line in enumerate(content.splitlines(), 1):
            if any(
                marker in line.upper()
                for marker in ("TODO", "FIXME", "XXX")
            ):
                todos.append(
                    f"{relative}:{number}: {line.strip()[:180]}"
                )
                if len(todos) >= 30:
                    break

        if (
            path.suffix.lower() in SOURCE_EXTENSIONS
            and len(source_files) < MAX_SOURCE_FILES
            and total_source_chars < MAX_SOURCE_CHARS
        ):
            remaining = MAX_SOURCE_CHARS - total_source_chars
            excerpt = content[:min(remaining, 3500)]

            numbered = "\n".join(
                f"{i}: {line}"
                for i, line in enumerate(excerpt.splitlines(), 1)
            )

            source_files.append({
                "path": relative,
                "content": numbered,
                "truncated": len(excerpt) < len(content),
            })

            total_source_chars += len(excerpt)

    return {
        "path": str(root),
        "readme": readme or "No README found.",
        "files": file_list,
        "commits": commits.splitlines() if commits else [],
        "status": status.splitlines() if status else [],
        "todos": todos[:30],
        "source_files": source_files,
    }
