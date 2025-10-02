"""Shared AI Request/Response Contract Models.

These Pydantic models define the stable JSON payload shapes exchanged over HTTP
between `sck-core-api` and `sck-core-ai`. They intentionally omit any
implementation specifics of Langflow, vector stores, or indexing internals.

All enclosing API responses exposed to UI must still wrap these in the standard
Core Automation envelope at the API layer::

    {
        "status": "success",
        "code": 200,
        "data": { ... one of the *Response models ... },
        "metadata": {"request_id": "..."}
    }

Guidelines:
    * Additive fields are non-breaking (models ignore unknown extras by config)
    * Rename / removal = breaking -> bump framework version & (future) contract_version
    * Keep this file lean; no network, logging, or heavy imports

Multi-Tenancy:
    * `tenant_client` (slug) may appear in some requests for scoping
    * `client_id` should usually be inferred from auth context at the API layer;
       it remains optional here for explicit diagnostic flows.

Example:
    >>> from core_framework.ai.contracts import TemplateGenerateRequest
    >>> req = TemplateGenerateRequest(prompt="Create an S3 bucket", tenant_client="core")
    >>> req.prompt
    'Create an S3 bucket'

"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AIBaseModel(BaseModel):
    """Base model with permissive extra handling for forward compatibility."""

    model_config = {
        "extra": "ignore",  # Unknown fields from newer server versions are ignored
        "populate_by_name": True,
        "validate_assignment": False,
    }


# ---------------------------------------------------------------------------
# Shared / Primitive Models
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    """Issue severity classification."""

    error = "error"
    warning = "warning"
    info = "info"
    suggestion = "suggestion"


class Issue(AIBaseModel):
    """Structured validation or analysis issue.

    Args:
        code: Stable machine-readable identifier (e.g., CFN rule id).
        message: Human-readable summary.
        severity: Severity level for UI highlighting & gating.
        line: Optional 1-based line number in original source.
        column: Optional 1-based column number in original source.
        hint: Short remediation string.
        context: Arbitrary structured metadata for tooling.
    """

    code: str = Field(..., description="Stable machine-readable identifier")
    message: str = Field(..., description="Human readable description")
    severity: Severity
    line: Optional[int] = Field(None, description="1-based line number if known")
    column: Optional[int] = Field(None, description="1-based column number if known")
    hint: Optional[str] = Field(None, description="Optional remediation guidance")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Arbitrary structured context for tooling")


class Cursor(AIBaseModel):
    """Editor cursor location (1-based line & column)."""

    line: int
    column: int


class CompletionItemKind(str, Enum):
    """Kinds of completion suggestions."""

    keyword = "keyword"
    snippet = "snippet"
    property = "property"
    itemvalue = "itemvalue"
    block = "block"
    reference = "reference"


class CompletionItem(AIBaseModel):
    """Single completion suggestion entry."""

    text: str
    kind: CompletionItemKind = CompletionItemKind.snippet
    label: Optional[str] = Field(default=None, description="Short label")
    detail: Optional[str] = Field(default=None, description="Short description")
    documentation: Optional[str] = Field(default=None, description="Markdown or plaintext docs")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Heuristic confidence score")


class SearchHitType(str, Enum):
    """Type of indexed content for search results."""

    documentation = "documentation"
    docstring = "docstring"
    symbol = "symbol"
    template = "template"


class SearchHit(AIBaseModel):
    """Search result item across documentation & symbols."""

    hit_type: SearchHitType
    title: str
    snippet: str
    score: float
    source_id: str = Field(..., description="Stable identifier (e.g. page path or symbol)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Generation / DSL Models
# ---------------------------------------------------------------------------


class TemplateGenerateRequest(AIBaseModel):
    """Request to generate or refine a DSL template from a natural language prompt."""

    prompt: str = Field(..., description="Natural language intent from user")
    tenant_client: str = Field(..., description="Active tenant slug")
    client_id: Optional[str] = Field(None, description="OAuth client_id context")
    previous_dsl: Optional[str] = Field(None, description="Prior version to allow diff-aware refinement")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="Optional constraints (regions, budgets, etc.)")


class GeneratedTemplateArtifact(AIBaseModel):
    """Generated DSL artifact plus rationale & warnings."""

    dsl: str
    rationale: str
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TemplateGenerateResponse(AIBaseModel):
    """Response containing generated DSL and any surfaced issues."""

    artifact: GeneratedTemplateArtifact
    issues: List[Issue] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class DSLValidateRequest(AIBaseModel):
    """Request to validate DSL syntax/semantics."""

    dsl: str
    strict: bool = True
    tenant_client: Optional[str] = None
    client_id: Optional[str] = None


class DSLValidateResponse(AIBaseModel):
    """Validation results for a DSL document."""

    valid: bool
    errors: List[Issue] = Field(default_factory=list)
    warnings: List[Issue] = Field(default_factory=list)
    suggestions: List[Issue] = Field(default_factory=list)
    inferred_metadata: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class CompletionRequest(AIBaseModel):
    """Request for code/DSL completion suggestions at a cursor position."""

    dsl: str
    cursor: Cursor
    context_window: Optional[int] = Field(40, description="Number of lines around cursor made available to LLM")
    max_items: int = 10
    mode: Optional[str] = Field(None, description="Optional hint: 'block' | 'property' | 'value'")


class CompletionResponse(AIBaseModel):
    """Completion suggestions and generation metadata."""

    items: List[CompletionItem]
    truncated: bool = False
    generation_ms: Optional[int] = None


class CompileRequest(AIBaseModel):
    """Request to compile DSL into CloudFormation (and optionally persist artefact)."""

    dsl: str
    tenant_client: str
    client_id: Optional[str] = None
    dry_run: bool = False
    include_intermediate: bool = False


class CompiledArtefact(AIBaseModel):
    """Compiled CloudFormation output with optional artefact metadata."""

    cloudformation: str
    artefact_id: Optional[str] = None
    resources_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompileResponse(AIBaseModel):
    """Compilation result indicating success and emitted artefact/issues."""

    success: bool
    artefact: Optional[CompiledArtefact] = None
    issues: List[Issue] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class CloudFormationValidateRequest(AIBaseModel):
    """Request to lint/validate raw CloudFormation template text."""

    cloudformation: str
    tenant_client: Optional[str] = None
    client_id: Optional[str] = None
    strict: bool = True


class CloudFormationFinding(Issue):
    """CloudFormation rule finding extending generic Issue."""

    rule_group: Optional[str] = Field(None, description="Classifier (security, cost)")


class CloudFormationValidateResponse(AIBaseModel):
    """CloudFormation validation result set."""

    valid: bool
    errors: List[CloudFormationFinding] = Field(default_factory=list)
    warnings: List[CloudFormationFinding] = Field(default_factory=list)
    suggestions: List[CloudFormationFinding] = Field(default_factory=list)
    risk_summary: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class SearchDocsRequest(AIBaseModel):
    """Full-text or semantic documentation query."""

    query: str
    top_k: int = 5
    tenant_client: Optional[str] = None


class SearchDocsResponse(AIBaseModel):
    """Documentation search response."""

    hits: List[SearchHit]
    total_indexed: int
    latency_ms: Optional[int] = None


class SearchSymbolsRequest(AIBaseModel):
    """Symbol (code/docstring/indexed) search query."""

    query: str
    top_k: int = 5


class SearchSymbolsResponse(AIBaseModel):
    """Symbol search response."""

    hits: List[SearchHit]
    latency_ms: Optional[int] = None


class OptimizeCloudFormationRequest(AIBaseModel):
    """(Future) Optimization request against CloudFormation template."""

    cloudformation: str
    goals: Optional[List[str]] = Field(default=None, description="High-level optimization focus areas")


class OptimizeCloudFormationResponse(AIBaseModel):
    """(Future) Optimization recommendations + diff preview."""

    recommendations: List[str] = Field(default_factory=list)
    diff_preview: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    # Enums / primitives
    "Severity",
    "Issue",
    "Cursor",
    "CompletionItemKind",
    "CompletionItem",
    "SearchHitType",
    "SearchHit",
    # Generation / DSL
    "TemplateGenerateRequest",
    "GeneratedTemplateArtifact",
    "TemplateGenerateResponse",
    "DSLValidateRequest",
    "DSLValidateResponse",
    "CompletionRequest",
    "CompletionResponse",
    # Compilation
    "CompileRequest",
    "CompiledArtefact",
    "CompileResponse",
    # CloudFormation validation
    "CloudFormationValidateRequest",
    "CloudFormationFinding",
    "CloudFormationValidateResponse",
    # Search
    "SearchDocsRequest",
    "SearchDocsResponse",
    "SearchSymbolsRequest",
    "SearchSymbolsResponse",
    # Optimization (future)
    "OptimizeCloudFormationRequest",
    "OptimizeCloudFormationResponse",
]
