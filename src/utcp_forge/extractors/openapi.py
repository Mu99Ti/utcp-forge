from __future__ import annotations
import json
import httpx
from pathlib import Path
from typing import Any, Dict, List
from utcp_forge.models.ir import RouteIR, ParamIR

class OpenApiExtractor:
    """Extracts RouteIR objects from OpenAPI / Swagger specs (local file or URL)."""

    def __init__(self, source: str):
        self.source = source

    def load_spec(self) -> Dict[str, Any]:
        if self.source.startswith("http://") or self.source.startswith("https://"):
            resp = httpx.get(self.source, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        path = Path(self.source)
        if not path.exists():
            raise FileNotFoundError(f"OpenAPI spec not found at: {self.source}")
        return json.loads(path.read_text(encoding="utf-8"))

    def scan(self) -> List[RouteIR]:
        spec = self.load_spec()
        routes: List[RouteIR] = []
        paths = spec.get("paths", {})

        for path_str, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() not in ("get", "post", "put", "delete", "patch", "options", "head"):
                    continue
                op_id = operation.get("operationId", f"{method.lower()}_{path_str.replace('/', '_')}")
                summary = operation.get("summary") or operation.get("description")
                tags = operation.get("tags", [])
                
                params: List[ParamIR] = []
                for p in operation.get("parameters", []):
                    params.append(
                        ParamIR(
                            name=p.get("name", "param"),
                            location=p.get("in", "query"),
                            required=p.get("required", False),
                            type_str=p.get("schema", {}).get("type", "string"),
                            description=p.get("description"),
                        )
                    )

                body_schema = None
                if "requestBody" in operation:
                    content = operation["requestBody"].get("content", {})
                    if "application/json" in content:
                        body_schema = content["application/json"].get("schema")

                auth_required = bool(operation.get("security") or spec.get("security"))

                routes.append(
                    RouteIR(
                        name=op_id,
                        path=path_str,
                        method=method.upper(),
                        handler_name=op_id,
                        file_path=self.source,
                        line_start=0,
                        line_end=0,
                        docstring=summary,
                        params=params,
                        body_schema=body_schema,
                        tags=tags,
                        auth_required=auth_required,
                        auth_type="bearer" if auth_required else None,
                    )
                )
        return routes
