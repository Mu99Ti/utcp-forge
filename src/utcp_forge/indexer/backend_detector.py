from __future__ import annotations
import ast
from pathlib import Path
from typing import List, Optional

class BackendDetector:
    """Discovers backend root directories in full-stack repositories, monorepos, or nested projects."""

    BACKEND_DIR_HINTS = [
        "backend",
        "server",
        "api",
        "services",
        "src",
        "app",
        "service",
    ]

    FRAMEWORK_INDICATORS = [
        "fastapi",
        "flask",
        "django",
        "starlette",
        "express",
        "nest",
        "koa",
    ]

    @classmethod
    def locate_backend_dirs(cls, root_dir: str) -> List[Path]:
        """Locates all plausible backend service directories within the target root."""
        root = Path(root_dir).resolve()
        if not root.is_dir():
            return [root]

        candidates: List[Path] = []

        # 1. Check if the root itself is directly a backend
        if cls._is_backend_directory(root):
            candidates.append(root)

        # 2. Check common subdirectories (e.g. backend/, server/, api/, services/*)
        for hint in cls.BACKEND_DIR_HINTS:
            sub = root / hint
            if sub.is_dir() and sub not in candidates:
                if cls._is_backend_directory(sub):
                    candidates.append(sub)

        # 3. Check for multi-service folders (e.g., services/* or apps/*)
        for parent_name in ("services", "apps", "packages"):
            parent_dir = root / parent_name
            if parent_dir.is_dir():
                for child in parent_dir.iterdir():
                    if child.is_dir() and cls._is_backend_directory(child):
                        if child not in candidates:
                            candidates.append(child)

        # 4. Fallback search: recursive search for main.py, app.py, server.js, wsgi.py
        if not candidates:
            for entrypoint in ("main.py", "app.py", "wsgi.py", "manage.py", "server.py"):
                for found_file in root.rglob(entrypoint):
                    if any(ignored in str(found_file) for ignored in ("venv", ".venv", "__pycache__", ".git", "node_modules", "tests")):
                        continue
                    parent = found_file.parent
                    if parent not in candidates and cls._is_backend_directory(parent):
                        candidates.append(parent)

        return candidates if candidates else [root]

    @classmethod
    def _is_backend_directory(cls, directory: Path) -> bool:
        """Determines if a directory contains backend route definitions or dependencies."""
        if any(ignored in str(directory) for ignored in ("venv", ".venv", "__pycache__", ".git", "node_modules", "tests")):
            return False

        # Check dependency files (requirements.txt, pyproject.toml, package.json, Pipfile)
        for dep_file in ("requirements.txt", "pyproject.toml", "Pipfile", "setup.py", "package.json"):
            f = directory / dep_file
            if f.is_file():
                try:
                    content = f.read_text(encoding="utf-8").lower()
                    if any(ind in content for ind in cls.FRAMEWORK_INDICATORS):
                        return True
                except Exception:
                    pass

        # Check for Python files containing FastAPI/Flask route decorators
        for py_file in directory.glob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if any(k in content for k in ("@app.get", "@app.post", "@router.get", "@router.post", "@blueprint.route")):
                    return True
            except Exception:
                pass

        # Check immediate subdirectories (e.g. app/ or api/)
        for sub in ("app", "api", "routes", "src"):
            sub_path = directory / sub
            if sub_path.is_dir():
                for py_file in sub_path.glob("*.py"):
                    try:
                        content = py_file.read_text(encoding="utf-8")
                        if any(k in content for k in ("@app.get", "@app.post", "@router.get", "@router.post", "@blueprint.route")):
                            return True
                    except Exception:
                        pass

        return False
