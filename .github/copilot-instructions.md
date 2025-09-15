# Copilot Instructions (Submodule: sck-core-framework)

- Tech: Python package (framework base).
- Precedence: Use local first; fallback to root `../../.github/...`.
- Conventions: Reference `../sck-core-ui/docs/backend-code-style.md` for shared backend rules.

## Contradiction Detection
- Ensure new utilities follow shared patterns; check root precedence.
- If conflict, warn with quote + source and provide options.
- Example: "Adding a non-thread-safe cache conflicts with concurrency guidance; use thread-safe InMemoryCache or Redis per docs."

## Standalone clone note
If cloned standalone, see:
- UI/backend conventions: https://github.com/eitssg/simple-cloud-kit/tree/develop/sck-core-ui/docs
- Root Copilot guidance: https://github.com/eitssg/simple-cloud-kit/blob/develop/.github/copilot-instructions.md
 
