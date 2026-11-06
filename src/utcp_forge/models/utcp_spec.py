from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class ApiKeyAuth(BaseModel):
    auth_type: str = "api_key"
    api_key: str  # e.g., "Bearer ${API_KEY}"
    var_name: str = "Authorization"
    location: str = "header"

class HttpCallTemplate(BaseModel):
    name: str
    call_template_type: str = "http"
    url: str
    http_method: str = "GET"
    content_type: str = "application/json"
    allowed_communication_protocols: List[str] = Field(default_factory=lambda: ["http"])
    auth: Optional[Union[ApiKeyAuth, Dict[str, Any]]] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    body_field: Optional[str] = "body"
    header_fields: List[str] = Field(default_factory=list)

class Tool(BaseModel):
    name: str
    description: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    tool_call_template: HttpCallTemplate

class UtcpManual(BaseModel):
    manual_version: str = "1.0.0"
    utcp_version: str = "1.0.2"
    tools: List[Tool] = Field(default_factory=list)
