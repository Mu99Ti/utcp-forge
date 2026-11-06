from __future__ import annotations
import ast
import re
from pathlib import Path
from typing import Optional

class HostDetector:
    """Detects host, domain, and port from project files, configs, and docker manifests."""

    @staticmethod
    def detect_base_url(root_dir: str, default: str = "http://localhost:8000") -> str:
        root = Path(root_dir)
        if not root.is_dir():
            return default

        # 1. Check .env, .env.example, .env.local
        for env_name in (".env", ".env.local", ".env.development", ".env.example"):
            env_file = root / env_name
            if env_file.exists():
                url = HostDetector._scan_env_file(env_file)
                if url:
                    return url

        # 2. Check docker-compose.yml or Dockerfile for port mapping
        for compose_name in ("docker-compose.yml", "docker-compose.yaml", "compose.yaml"):
            compose_file = root / compose_name
            if compose_file.exists():
                port = HostDetector._scan_compose_file(compose_file)
                if port:
                    return f"http://localhost:{port}"

        # 3. Check settings.py or config.py for port/host assignments
        for config_path in root.rglob("*.py"):
            if config_path.name in ("config.py", "settings.py", "constants.py", "main.py"):
                if any(p in str(config_path) for p in ("venv", ".venv", "__pycache__")):
                    continue
                url = HostDetector._scan_python_config(config_path)
                if url:
                    return url

        return default

    @staticmethod
    def _scan_env_file(env_file: Path) -> Optional[str]:
        try:
            content = env_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip().upper()
                val = val.strip().strip("'\"")
                if key in ("BASE_URL", "DOMAIN", "API_URL", "SERVER_URL", "PUBLIC_URL", "NEXT_PUBLIC_API_URL"):
                    if val.startswith("http://") or val.startswith("https://"):
                        return val
                    return f"https://{val}"
                if key in ("PORT", "SERVER_PORT", "APP_PORT") and val.isdigit():
                    return f"http://localhost:{val}"
        except Exception:
            pass
        return None

    @staticmethod
    def _scan_compose_file(compose_file: Path) -> Optional[str]:
        try:
            content = compose_file.read_text(encoding="utf-8")
            match = re.search(r'["\']?(\d{2,5}):(\d{2,5})["\']?', content)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    @staticmethod
    def _scan_python_config(py_file: Path) -> Optional[str]:
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id.upper()
                            if var_name in ("PORT", "SERVER_PORT") and isinstance(node.value, ast.Constant):
                                return f"http://localhost:{node.value.value}"
                            if var_name in ("BASE_URL", "SERVER_HOST", "DOMAIN") and isinstance(node.value, ast.Constant):
                                val = str(node.value.value)
                                if val.startswith("http://") or val.startswith("https://"):
                                    return val
                                return f"https://{val}"
        except Exception:
            pass
        return None
