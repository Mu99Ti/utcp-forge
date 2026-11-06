from __future__ import annotations
import ast
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ModelFieldIR(BaseModel):
    name: str
    type_str: str
    required: bool = True
    default: Optional[Any] = None
    description: Optional[str] = None

class ModelIR(BaseModel):
    name: str
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    fields: List[ModelFieldIR] = Field(default_factory=list)

class SymbolTable:
    """In-memory symbol table mapping classes, Pydantic models, and functions."""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.models: Dict[str, ModelIR] = {}
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.index_codebase()

    def index_codebase(self) -> None:
        for py_file in self.root_dir.rglob("*.py"):
            if any(p in str(py_file) for p in ("venv", ".venv", "__pycache__", ".git")):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))
                self._index_file_ast(tree, str(py_file))
            except Exception:
                continue

    def _index_file_ast(self, tree: ast.AST, file_path: str) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) for b in node.bases]
                is_pydantic = any("BaseModel" in b or "Schema" in b for b in bases)
                fields: List[ModelFieldIR] = []
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        field_name = item.target.id
                        type_str = ast.unparse(item.annotation)
                        default_val = ast.unparse(item.value) if item.value else None
                        fields.append(
                            ModelFieldIR(
                                name=field_name,
                                type_str=type_str,
                                required=(default_val is None),
                                default=default_val
                            )
                        )
                docstring = ast.get_docstring(node)
                self.models[node.name] = ModelIR(
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno,
                    docstring=docstring,
                    fields=fields
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions[node.name] = {
                    "file_path": file_path,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "docstring": ast.get_docstring(node)
                }

    def resolve_model_schema(self, type_name: str) -> Optional[Dict[str, Any]]:
        clean_name = type_name.split("[")[-1].replace("]", "").strip()
        model = self.models.get(clean_name)
        if not model:
            return None
        
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for f in model.fields:
            type_mapping = "string"
            t_lower = f.type_str.lower()
            if any(k in t_lower for k in ("int", "float", "number")):
                type_mapping = "number"
            elif "bool" in t_lower:
                type_mapping = "boolean"
            elif any(k in t_lower for k in ("list", "sequence", "set")):
                type_mapping = "array"

            properties[f.name] = {
                "type": type_mapping,
                "description": f.description or f"Field '{f.name}' of type {f.type_str}"
            }
            if f.required:
                required.append(f.name)

        return {
            "type": "object",
            "title": model.name,
            "description": model.docstring or f"Schema for {model.name}",
            "properties": properties,
            "required": required
        }
