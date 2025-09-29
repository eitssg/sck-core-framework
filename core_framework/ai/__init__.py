"""AI Service Shared Namespace.

This namespace hosts lightweight, cross-service contract models that define the
request/response payloads exchanged between:

    * sck-core-api  (FastAPI/Lambda facade making HTTP calls to AI service)
    * sck-core-ai   (containerized AI + Langflow orchestration service)
    * (future) developer tooling or editors that wish to construct strongly
      typed requests without depending on AI internal implementation details.

Only boundary (public) DTOs live here. Internal AI/runtime, indexing, Langflow
pipeline, embedding, or optimization experimental models stay inside
`sck-core-ai` and must NOT be added here until they stabilize as external
contracts.

Design principles:
    - Zero heavy dependencies (Pydantic + stdlib only)
    - Backwards compatible additions (responses tolerate unknown fields)
    - Multi-tenant safe (client_id implicit from auth; tenant slug explicit)
    - Versionable (future: add contract_version if/when breaking changes planned)

Import style (explicit is preferred to avoid broad surface pollution):

    from core_framework.ai.contracts import TemplateGenerateRequest, TemplateGenerateResponse

"""

from .contracts import *  # noqa: F401,F403 (re-export intentional for namespace consumers)

__all__ = [  # type: ignore[var-annotated]
    *[name for name in globals().keys() if not name.startswith("_")],
]
