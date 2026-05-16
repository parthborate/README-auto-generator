import os
import sys
import pathlib
import subprocess
import anthropic
from dotenv import load_dotenv

# Load the API key from .env into environment variables
load_dotenv()

# Create the Claude client. It automatically reads ANTHROPIC_API_KEY from env.
client = anthropic.Anthropic()

# File extensions we care about. Anything else gets skipped.
RELEVANT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".md", ".json", ".toml", ".yaml", ".yml",
    ".txt", ".sh", ".rs", ".go", ".rb", ".java",
}

# Maximum file size we'll include (in bytes). Skip giant generated files.
MAX_FILE_SIZE = 50_000  # 50 KB

# Folders to skip entirely (in addition to anything .gitignore says to skip).
SKIP_FOLDERS = {
    "node_modules", "venv", ".venv", "env", "__pycache__",
    "dist", "build", ".next", ".nuxt", "out", "target",
    "vendor", ".git", ".idea", ".vscode", "coverage",
    ".pytest_cache", ".mypy_cache", "site-packages",
    ".tox", "htmlcov", ".cache", "docs/_build",
}

# Max characters of context to send to Claude.
# ~200,000 chars ≈ 50,000 tokens — plenty for any README.
MAX_CONTEXT_CHARS = 200_000

# Priority files — always include these first if they exist.
# A README written from just these is usually 90% as good as one written from the whole repo.
PRIORITY_FILENAMES = {
    "README.md", "readme.md", "README.rst",
    "package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod",
    "setup.py", "setup.cfg", "Pipfile",
    "main.py", "app.py", "index.js", "index.ts", "server.py", "manage.py",
    "Dockerfile", "docker-compose.yml",
    ".env.example",
}


def walk_repo(root_path):
    """
    Walk through the repo using git's view of what's tracked + untracked-but-not-ignored.
    This automatically respects .gitignore. Falls back to a manual walk if not a git repo.
    Returns {relative_path: file_contents}.
    """
    root = pathlib.Path(root_path)
    
    # Try git first — it's the most correct source of "what's in this project"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, check=True
        )
        candidate_paths = [root / line for line in result.stdout.strip().split("\n") if line]
        print(f"   Using git to list files (respecting .gitignore).")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repo, or git not installed — fall back to manual walk
        print(f"   Not a git repo, doing manual walk.")
        candidate_paths = list(root.rglob("*"))
    
    files = {}
    for path in candidate_paths:
        if not path.is_file():
            continue
        # Defense in depth: still skip junk folders even if git missed them
        if any(part in SKIP_FOLDERS or part.startswith(".") for part in path.parts):
            continue
        if path.suffix not in RELEVANT_EXTENSIONS:
            continue
        if path.stat().st_size > MAX_FILE_SIZE:
            continue
        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue
        files[str(path.relative_to(root))] = content
    
    return files


def build_context(files):
    """
    Build a context string from files, prioritizing important ones,
    and stop adding files once we hit MAX_CONTEXT_CHARS.
    """
    def priority(path):
        name = pathlib.Path(path).name
        if name in PRIORITY_FILENAMES:
            return (0, path)  # priority files first
        depth = path.count("/")
        return (1 + depth, path)  # then by depth (root files before deep ones)
    
    sorted_files = sorted(files.items(), key=lambda kv: priority(kv[0]))
    
    sections = []
    total_chars = 0
    included = 0
    skipped = 0
    
    for filename, contents in sorted_files:
        section = f"### File: {filename}\n```\n{contents}\n```"
        if total_chars + len(section) > MAX_CONTEXT_CHARS:
            skipped += 1
            continue
        sections.append(section)
        total_chars += len(section)
        included += 1
    
    print(f"   Including {included} files in prompt ({total_chars:,} chars). Skipped {skipped} to fit budget.")
    return "\n\n".join(sections)


def generate_readme(repo_path):
    """
    Main function: take a repo path, return a generated README as a string.
    """
    print(f"📂 Walking repo at {repo_path}...")
    files = walk_repo(repo_path)
    print(f"   Found {len(files)} relevant files.")
    
    if not files:
        return "# Empty Repo\n\nNo readable code files found."
    
    context = build_context(files)
    
    print("🤖 Calling Claude...")
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a senior software engineer. Read the repository files below "
                    "and write a clean, professional README.md for this project. Include "
                    "these sections in this order: Overview, Features, Installation, Usage, "
                    "Examples, Project Structure, License (assume MIT if unsure).\n\n"
                    "Use proper markdown formatting. Don't add any preamble — start directly "
                    "with `# <Project Name>`.\n\n"
                    f"{context}"
                )
            }
        ]
    )
    
    return message.content[0].text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate.py /path/to/repo")
        sys.exit(1)
    
    # expanduser() handles ~, resolve() makes it absolute and clean
    repo_path = pathlib.Path(sys.argv[1]).expanduser().resolve()
    
    # Fail fast with a clear error if the path is wrong
    if not repo_path.exists():
        print(f"❌ Path does not exist: {repo_path}")
        sys.exit(1)
    if not repo_path.is_dir():
        print(f"❌ Not a directory: {repo_path}")
        sys.exit(1)
    
    readme_text = generate_readme(str(repo_path))
    
    output_path = repo_path / "README.generated.md"
    output_path.write_text(readme_text)
    print(f"✅ Saved to {output_path}")
