from __future__ import annotations
import ast
from pathlib import Path
from typing import Dict, Optional

class CodeSkeletonizer:
    """Extracts compact signatures, models, and handler skeletons to minimize LLM token spend."""

    @staticmethod
    def get_handler_skeleton(file_path: str, line_start: int, line_end: int) -> str:
        """Reads only the target handler lines, stripping extraneous bulk."""
        p = Path(file_path)
        if not p.exists() or line_start <= 0:
            return ""
        lines = p.read_text(encoding="utf-8").splitlines()
        # Grab lines with 5 lines of upper context (decorators/docstrings)
        start_idx = max(0, line_start - 1)
        end_idx = min(len(lines), line_end)
        return "\n".join(lines[start_idx:end_idx])

    @staticmethod
    def extract_pydantic_skeletons(file_path: str) -> Dict[str, str]:
        """Finds Pydantic model class declarations and returns clean field-level signatures."""
        p = Path(file_path)
        if not p.exists():
            return {}
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
            models = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if inherits from BaseModel
                    bases = [ast.unparse(b) for b in node.bases]
                    if any("BaseModel" in b or "Schema" in b for b in bases):
                        # Extract only annotated fields and docstrings
                        fields = []
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign):
                                fields.append(f"  {ast.unparse(item)}")
                        doc = ast.get_docstring(node)
                        doc_str = f'  """{doc}"""\n' if doc else ""
                        models[node.name] = f"class {node.name}(BaseModel):\n{doc_str}" + "\n".join(fields)
            return models
        except Exception:
            return {}
