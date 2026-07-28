"""
Repository Traversal, Language Detection, and File Enumeration.
"""

import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Union

from cig.parser.models import LoadedFile

DEFAULT_IGNORE_PATTERNS = [
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
    "*.egg-info",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dll",
    "*.exe",
    ".DS_Store",
]

DEFAULT_LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".go": "go",
    ".rs": "rust",
}


class RepoLoader:
    """Handles loading files from a local repository directory with language detection and filtering."""

    def __init__(
        self,
        repo_path: Union[str, Path],
        ignore_patterns: Optional[List[str]] = None,
        language_map: Optional[Dict[str, str]] = None,
    ) -> None:
        self.repo_path = Path(repo_path).resolve()
        self.ignore_patterns = list(DEFAULT_IGNORE_PATTERNS)
        if ignore_patterns:
            self.ignore_patterns.extend(ignore_patterns)
        
        self.language_map = dict(DEFAULT_LANGUAGE_MAP)
        if language_map:
            self.language_map.update(language_map)

    def is_ignored(self, rel_path: Path) -> bool:
        """Check if a relative path matches any ignore pattern or directory."""
        parts = rel_path.parts
        rel_str = rel_path.as_posix()

        for pattern in self.ignore_patterns:
            # Check pattern against relative path string or any directory component
            if fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch(rel_path.name, pattern):
                return True
            for part in parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
        return False

    def detect_language(self, path: Path) -> str:
        """Detect programming language based on file extension."""
        ext = path.suffix.lower()
        return self.language_map.get(ext, "unknown")

    def load_files(self) -> List[LoadedFile]:
        """
        Enumerate and read all non-ignored source files from the repository.
        Returns a deterministically sorted list of LoadedFile instances.
        """
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")

        loaded_files: List[LoadedFile] = []

        for path in self.repo_path.rglob("*"):
            if not path.is_file():
                continue
            
            try:
                rel_path = path.relative_to(self.repo_path)
            except ValueError:
                continue

            if self.is_ignored(rel_path):
                continue

            rel_posix = rel_path.as_posix()
            lang = self.detect_language(path)

            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                size_bytes = path.stat().st_size
                loaded_files.append(
                    LoadedFile(
                        file_path=rel_posix,
                        absolute_path=str(path.resolve()),
                        language=lang,
                        content=content,
                        size_bytes=size_bytes,
                    )
                )
            except Exception:
                # Skip unreadable binary or corrupt files
                continue

        # Sort deterministically by relative file path
        loaded_files.sort(key=lambda f: f.file_path)
        return loaded_files
