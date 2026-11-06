from __future__ import annotations
import json
from pathlib import Path
from typing import List, Optional
from utcp_forge.models.ir import EnrichedToolIR
from utcp_forge.models.utcp_spec import UtcpManual, Tool, HttpCallTemplate, ApiKeyAuth

class UtcpCompiler:
    """Compiles enriched tools into a valid UTCP 1.0 JSON manual."""

    @staticmethod
    def compile(tools: List[EnrichedToolIR], base_url: str = "https://api.example.com") -> UtcpManual:
        utcp_tools: List[Tool] = []

        for t in tools:
            if not t.should_include:
                continue

            auth = None
            if t.auth_header and t.auth_env_var:
                auth = ApiKeyAuth(
                    api_key=f"Bearer ${{{t.auth_env_var}}}",
                    var_name=t.auth_header,
                    location="header"
                )

            template = HttpCallTemplate(
                name=t.name,
                call_template_type="http",
                url=f"{base_url.rstrip('/')}{t.path}",
                http_method=t.method,
                allowed_communication_protocols=["http"],
                auth=auth
            )

            tool = Tool(
                name=t.name,
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
