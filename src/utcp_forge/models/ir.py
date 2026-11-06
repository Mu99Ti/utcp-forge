from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ParamIR(BaseModel):
    name: str
    location: str = "query"  # query, path, header, body
    type_str: str = "string"
    required: bool = True
    default: Optional[Any] = None
    description: Optional[str] = None

class RouteIR(BaseModel):
    name: str
    path: str
    method: str
    handler_name: str
    file_path: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    params: List[ParamIR] = Field(default_factory=list)
    body_schema: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)
    auth_required: bool = False
    auth_type: Optional[str] = None  # bearer, api_key, basic, oauth2
    auth_header: str = "Authorization"

class EnrichedToolIR(BaseModel):
    name: str
    path: str
    method: str
    description: str
    intent: str
    is_destructive: bool = False
    tags: List[str] = Field(default_factory=list)
    inputs_schema: Dict[str, Any] = Field(default_factory=dict)
    outputs_schema: Dict[str, Any] = Field(default_factory=dict)
    auth_header: Optional[str] = None
    auth_env_var: Optional[str] = None
    should_include: bool = True
    exclusion_reason: Optional[str] = None
