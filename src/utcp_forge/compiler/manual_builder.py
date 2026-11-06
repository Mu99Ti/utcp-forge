from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List, Optional
from utcp_forge.models.ir import EnrichedToolIR
from utcp_forge.models.utcp_spec import UtcpManual, Tool, HttpCallTemplate, ApiKeyAuth

class UtcpCompiler:
    """Compiles enriched tools into a valid UTCP 1.0 JSON manual following expert namespacing rules."""

    @staticmethod
    def format_tool_name(manual_name: str, path: str, method: str) -> str:
        """Enforces <manual_name>.<resource>_<action> with collision resistance."""
        clean_manual = re.sub(r"[^a-zA-Z0-9_]", "_", manual_name.lower())
        
        # Clean path segments
        path_parts = [p.strip("{}") for p in path.strip("/").split("/") if p and p not in ("api", "v1", "v2", "v3")]
        resource = path_parts[0] if path_parts else "root"
        sub_action = "_".join(path_parts[1:]) if len(path_parts) > 1 else ""

        method_action = method.lower()
        if method_action == "post":
            method_action = "create"
        elif method_action == "delete":
            method_action = "delete"
        elif method_action in ("put", "patch"):
            method_action = "update"
        elif method_action == "get":
            method_action = "get" if sub_action else "list"

        action_name = f"{resource}_{method_action}"
        if sub_action:
            action_name = f"{action_name}_by_{sub_action}"

        clean_action = re.sub(r"[^a-zA-Z0-9_]+", "_", action_name).strip("_")
        return f"{clean_manual}.{clean_action}"

    @staticmethod
    def format_auth_variable(manual_name: str, raw_var: str = "API_KEY") -> str:
        """Enforces UTCP v1.0 namespacing rule: manual_name duplicated underscore __ VAR_NAME."""
        clean_manual = re.sub(r"[^a-zA-Z0-9_]", "_", manual_name.lower())
        clean_var = re.sub(r"[^a-zA-Z0-9_]", "_", raw_var.upper())
        return f"{clean_manual}__{clean_var}"

    @classmethod
    def compile(
        cls,
        tools: List[EnrichedToolIR],
        manual_name: str = "api_service",
        base_url: str = "https://api.example.com"
    ) -> UtcpManual:
        utcp_tools: List[Tool] = []
        used_names: set[str] = set()

        for t in tools:
            if not t.should_include:
                continue

            base_tool_name = cls.format_tool_name(manual_name, t.path, t.method)
            namespaced_tool_name = base_tool_name
            counter = 2
            while namespaced_tool_name in used_names:
                namespaced_tool_name = f"{base_tool_name}_{counter}"
                counter += 1
            used_names.add(namespaced_tool_name)

            auth = None
            if t.auth_header:
                var_name = cls.format_auth_variable(manual_name, t.auth_env_var or "API_KEY")
                auth = ApiKeyAuth(
                    api_key=f"Bearer ${{{var_name}}}",
                    var_name=t.auth_header,
                    location="header"
                )

            # Build URL ensuring single slash
            full_url = f"{base_url.rstrip('/')}/{t.path.lstrip('/')}"

            template = HttpCallTemplate(
                name=namespaced_tool_name,
                call_template_type="http",
                url=full_url,
                http_method=t.method,
                allowed_communication_protocols=["http"],
                auth=auth
            )

            tool = Tool(
                name=namespaced_tool_name,
                description=t.description,
                tags=t.tags,
                inputs=t.inputs_schema,
                outputs={"type": "object", "description": "JSON response from endpoint"},
                tool_call_template=template
            )
            utcp_tools.append(tool)

        return UtcpManual(
            manual_version="1.0.0",
            utcp_version="1.0.2",
            tools=utcp_tools
        )

    @staticmethod
    def save_to_file(manual: UtcpManual, output_path: str) -> None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(manual.model_dump(exclude_none=True), indent=2), encoding="utf-8")
