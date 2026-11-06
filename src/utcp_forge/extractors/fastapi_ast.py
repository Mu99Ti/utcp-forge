from __future__ import annotations
import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from utcp_forge.models.ir import RouteIR, ParamIR

class FastAPIASTExtractor:
    """Zero-overhead AST scanner for FastAPI & Starlette applications."""

    HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.router_prefixes: Dict[str, str] = {}
        self._discover_router_prefixes()

    def _discover_router_prefixes(self) -> None:
        """Finds router prefixes e.g. APIRouter(prefix="/users") or app.include_router(..., prefix="/api")."""
        for py_file in self.root_dir.rglob("*.py"):
            if any(p in str(py_file) for p in ("venv", ".venv", "__pycache__", ".git")):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))
                for node in ast.walk(tree):
                    # router = APIRouter(prefix="/users")
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                                func_name = ast.unparse(node.value.func)
                                if "APIRouter" in func_name:
                                    for kw in node.value.keywords:
                                        if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                            self.router_prefixes[target.id] = str(kw.value.value)
            except Exception:
                continue

    def scan(self) -> List[RouteIR]:
        routes: List[RouteIR] = []
        for py_file in self.root_dir.rglob("*.py"):
            if any(p in str(py_file) for p in ("venv", ".venv", "__pycache__", ".git")):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))
                file_routes = self._extract_routes_from_tree(tree, py_file)
                routes.extend(file_routes)
            except Exception:
                continue
        return routes

    def _extract_routes_from_tree(self, tree: ast.AST, file_path: Path) -> List[RouteIR]:
        routes: List[RouteIR] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    route_info = self._parse_route_decorator(decorator)
                    if route_info:
                        docstring = ast.get_docstring(node)
                        params = self._extract_params(node, route_info["path"])
                        auth_required, auth_type = self._detect_auth(node)

                        route = RouteIR(
                            name=f"{route_info['method'].lower()}_{node.name}",
                            path=route_info["path"],
                            method=route_info["method"].upper(),
                            handler_name=node.name,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            docstring=docstring,
                            params=params,
                            tags=route_info.get("tags", []),
                            auth_required=auth_required,
                            auth_type=auth_type,
                        )
                        routes.append(route)
        return routes

    def _parse_route_decorator(self, decorator: ast.AST) -> Optional[Dict[str, Any]]:
        # Handles @app.get('/path') or @router.post('/path', tags=['users'])
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            method = decorator.func.attr.lower()
            caller_name = ast.unparse(decorator.func.value)
            if method in self.HTTP_METHODS:
                path = "/"
                if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                    path = decorator.args[0].value
                elif decorator.args and isinstance(decorator.args[0], ast.JoinedStr):
                    # Handle f-strings or constants
                    path = ast.unparse(decorator.args[0])

                # Prepend router prefix if found
                prefix = self.router_prefixes.get(caller_name, "")
                if prefix and not path.startswith(prefix):
                    path = f"{prefix.rstrip('/')}/{path.lstrip('/')}"
                if not path.startswith("/"):
                    path = f"/{path}"

                tags = []
                for kw in decorator.keywords:
                    if kw.arg == "tags" and isinstance(kw.value, ast.List):
                        tags = [elt.value for elt in kw.value.elts if isinstance(elt, ast.Constant)]
                return {"method": method, "path": path, "tags": tags}
        return None

    def _extract_params(self, node: ast.FunctionDef | ast.AsyncFunctionDef, route_path: str) -> List[ParamIR]:
        params: List[ParamIR] = []
        path_param_names = set(re.findall(r"\{([a-zA-Z0-9_]+)\}", route_path))

        for arg in node.args.args:
            name = arg.arg
            if name in ("self", "cls", "request", "db"):
                continue
            type_str = "string"
            if arg.annotation:
                type_str = ast.unparse(arg.annotation)
            
            # Determine parameter location
            if name in path_param_names:
                location = "path"
            elif any(k in type_str for k in ("BaseModel", "Schema", "Body", "Payload", "Create", "Update")):
                location = "body"
            else:
                location = "query"

            params.append(ParamIR(name=name, location=location, type_str=type_str, required=True))
        return params

    def _detect_auth(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[bool, Optional[str]]:
        for default in node.args.defaults:
            expr = ast.unparse(default)
            if "Depends" in expr:
                if any(w in expr.lower() for w in ("auth", "user", "token", "jwt", "bearer", "api_key", "security", "permission")):
                    return True, "bearer"
        return False, None
