from __future__ import annotations
import json
import os
from typing import Any, Dict, List, Optional
from utcp_forge.models.ir import RouteIR, EnrichedToolIR
from utcp_forge.agent.skeletonizer import CodeSkeletonizer
from utcp_forge.indexer.symbol_table import SymbolTable

try:
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

AGENT_SYSTEM_PROMPT = """You are an expert AI Agent Architect specializing in UTCP (Universal Tool Calling Protocol).
Your task is to analyze backend API routes and generate precise, agent-friendly tool definitions adhering to UTCP namespacing rules.

For each route, decide:
1. `should_include`: false for internal health checks (/health, /metrics), debug routes, or static files. true for business APIs.
2. `description`: An agent-actionable description explaining:
   - What the tool does
   - WHEN an agent should choose to call it
   - Key pre-conditions or side-effects (e.g., "Charges credit card", "Modifies user balance")
3. `is_destructive`: true if it performs DELETE or state mutations.
4. `auth_env_var`: Raw variable name suffix (e.g., "API_KEY" or "AUTH_TOKEN") without manual prefix.
"""

class RouteInvestigatorAgent:
    """Cost-efficient LangChain DeepAgent investigator with deterministic symbol resolution."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        symbol_table: Optional[SymbolTable] = None,
        temperature: float = 0.0
    ):
        self.model_name = model_name
        self.symbol_table = symbol_table
        self.llm = None
        
        target_api_key = api_key or os.getenv("OPENAI_API_KEY")
        target_base_url = base_url or os.getenv("OPENAI_API_BASE")

        if HAS_LANGCHAIN and (target_api_key or target_base_url):
            try:
                self.llm = ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    openai_api_base=target_base_url,
                    openai_api_key=target_api_key or "placeholder_key"
                )
            except Exception:
                self.llm = None

    def investigate(self, route: RouteIR) -> EnrichedToolIR:
        # 1. Deterministic heuristic filter (Zero token cost)
        if any(h in route.path.lower() for h in ("/health", "/metrics", "/docs", "/openapi.json", "/favicon.ico")):
            return EnrichedToolIR(
                name=route.name,
                path=route.path,
                method=route.method,
                description="Internal health check endpoint.",
                intent="system_monitoring",
                should_include=False,
                exclusion_reason="System/Internal endpoint"
            )

        # 2. Extract AST skeleton (minimal tokens)
        skeleton = ""
        if route.file_path and route.line_start > 0:
            skeleton = CodeSkeletonizer.get_handler_skeleton(route.file_path, route.line_start, route.line_end)

        # 3. Resolve dependent schemas deterministically from SymbolTable if available
        resolved_body_schema = route.body_schema
        if self.symbol_table and not resolved_body_schema:
            for p in route.params:
                if p.location == "body":
                    resolved_body_schema = self.symbol_table.resolve_model_schema(p.type_str)
                    if resolved_body_schema:
                        break

        # 4. If LLM is configured, enrich context
        if self.llm:
            try:
                return self._investigate_with_llm(route, skeleton, resolved_body_schema)
            except Exception:
                pass

        # 5. Deterministic fallback
        return self._heuristic_fallback(route, skeleton, resolved_body_schema)

    def _investigate_with_llm(self, route: RouteIR, skeleton: str, body_schema: Optional[Dict[str, Any]]) -> EnrichedToolIR:
        route_summary = {
            "name": route.name,
            "path": route.path,
            "method": route.method,
            "docstring": route.docstring,
            "parameters": [p.model_dump() for p in route.params],
            "resolved_schema": body_schema,
            "auth_required": route.auth_required,
            "code_skeleton": skeleton[:1000] if skeleton else "N/A"
        }

        user_content = f"Analyze this API route and output valid JSON:\n{json.dumps(route_summary, indent=2)}"
        messages = [
            SystemMessage(content=AGENT_SYSTEM_PROMPT),
            HumanMessage(content=user_content)
        ]

        structured_llm = self.llm.bind(response_format={"type": "json_object"})
        response = structured_llm.invoke(messages)
        data = json.loads(response.content)

        return EnrichedToolIR(
            name=data.get("name", route.name),
            path=route.path,
            method=route.method,
            description=data.get("description", route.docstring or f"Execute {route.method} on {route.path}"),
            intent=data.get("intent", route.name),
            is_destructive=data.get("is_destructive", route.method in ("DELETE", "POST")),
            tags=route.tags or ["api"],
            inputs_schema=self._build_inputs_schema(route, body_schema),
            auth_header=route.auth_header if route.auth_required else None,
            auth_env_var=data.get("auth_env_var", "API_KEY" if route.auth_required else None),
            should_include=data.get("should_include", True),
            exclusion_reason=data.get("exclusion_reason")
        )

    def _heuristic_fallback(self, route: RouteIR, skeleton: str, body_schema: Optional[Dict[str, Any]]) -> EnrichedToolIR:
        desc = route.docstring or f"Calls {route.method} {route.path} to interact with {route.handler_name}."
        if route.method == "GET":
            desc = f"Retrieve data from {route.path}. Safe to call."
        elif route.method == "POST":
            desc = f"Create or submit data to {route.path}. Pre-conditions: Ensure required parameters are provided."
        elif route.method == "DELETE":
            desc = f"Delete or remove resource at {route.path}. Destructive operation."

        return EnrichedToolIR(
            name=route.name,
            path=route.path,
            method=route.method,
            description=desc,
            intent=route.handler_name,
            is_destructive=route.method in ("DELETE", "POST"),
            tags=route.tags or ["default"],
            inputs_schema=self._build_inputs_schema(route, body_schema),
            auth_header=route.auth_header if route.auth_required else None,
            auth_env_var="API_KEY" if route.auth_required else None,
            should_include=True
        )

    def _build_inputs_schema(self, route: RouteIR, body_schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for p in route.params:
            if p.location == "body" and body_schema:
                properties["body"] = body_schema
                required.append("body")
                continue
            properties[p.name] = {
                "type": "string" if p.type_str in ("str", "string") else "number" if p.type_str in ("int", "float", "number") else "string",
                "description": p.description or f"Parameter '{p.name}' ({p.location})"
            }
            if p.required:
                required.append(p.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
