from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class FileDiff:
    """Represents the diff for a single file in a PR."""
    filename: str
    status: str                  # added, modified, deleted, renamed
    language: str                # inferred from file extension
    additions: int
    deletions: int
    patch: str                   # the actual diff text
    is_test_file: bool
    is_config_file: bool


@dataclass
class ParsedPR:
    """Fully structured PR ready for agent analysis."""
    pr_number: int
    title: str
    description: str
    author: str
    base_branch: str
    head_branch: str
    repo_name: str
    commit_messages: list[str]
    files: list[FileDiff]
    total_additions: int
    total_deletions: int
    changed_languages: list[str]

    @property
    def total_files_changed(self) -> int:
        return len(self.files)

    @property
    def test_files(self) -> list[FileDiff]:
        return [f for f in self.files if f.is_test_file]

    @property
    def source_files(self) -> list[FileDiff]:
        return [f for f in self.files if not f.is_test_file and not f.is_config_file]

    def get_full_diff_text(self) -> str:
        """Returns all diffs concatenated — used as agent context."""
        parts = []
        for f in self.files:
            parts.append(f"=== {f.filename} ({f.status}) ===")
            parts.append(f.patch or "(binary or empty file)")
            parts.append("")
        return "\n".join(parts)

    def get_diff_by_language(self, language: str) -> list[FileDiff]:
        return [f for f in self.files if f.language == language]


# ── helpers ──────────────────────────────────────────────────────────────────

LANGUAGE_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript", ".tsx": "TypeScript", ".java": "Java",
    ".go": "Go", ".rs": "Rust", ".cpp": "C++", ".c": "C",
    ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".kt": "Kotlin", ".scala": "Scala", ".sh": "Shell",
    ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
    ".toml": "TOML", ".md": "Markdown", ".sql": "SQL",
    ".html": "HTML", ".css": "CSS", ".tf": "Terraform",
}

TEST_PATTERNS = re.compile(
    r"(test_|_test\.|\.test\.|\.spec\.|/tests/|/test/|/__tests__/)",
    re.IGNORECASE,
)

CONFIG_PATTERNS = re.compile(
    r"\.(yaml|yml|json|toml|ini|cfg|conf|env|lock)$|"
    r"(dockerfile|docker-compose|makefile|\.github/)",
    re.IGNORECASE,
)


def infer_language(filename: str) -> str:
    for ext, lang in LANGUAGE_MAP.items():
        if filename.endswith(ext):
            return lang
    return "Unknown"


def parse_file_diff(github_file) -> FileDiff:
    """Convert a PyGithub File object into our FileDiff dataclass."""
    filename = github_file.filename
    return FileDiff(
        filename=filename,
        status=github_file.status,
        language=infer_language(filename),
        additions=github_file.additions,
        deletions=github_file.deletions,
        patch=github_file.patch or "",
        is_test_file=bool(TEST_PATTERNS.search(filename)),
        is_config_file=bool(CONFIG_PATTERNS.search(filename)),
    )