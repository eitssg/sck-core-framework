# Copilot Instructions (Submodule: sck-core-framework)

- Tech: Python package (framework base).
- Precedence: Use local first; fallback to root `../../.github/...`.
- Conventions: Reference `../sck-core-ui/docs/backend-code-style.md` for shared backend rules.

## Google Docstring Requirements
**MANDATORY**: All docstrings must use Google-style format for Sphinx documentation generation:
- Use Google-style docstrings with proper Args/Returns/Example sections
- Napoleon extension will convert Google format to RST for Sphinx processing
- Avoid direct RST syntax (`::`, `:param:`, etc.) in docstrings - use Google format instead
- Example sections should use `>>>` for doctests or simple code examples
- This ensures proper IDE interpretation while maintaining clean Sphinx documentation

## Contradiction Detection
- Ensure new utilities follow shared patterns; check root precedence.
- If conflict, warn with quote + source and provide options.
- Example: "Adding a non-thread-safe cache conflicts with concurrency guidance; use thread-safe InMemoryCache or Redis per docs."

## Standalone clone note
If cloned standalone, see:
- UI/backend conventions: https://github.com/eitssg/simple-cloud-kit/tree/develop/sck-core-ui/docs
- Root Copilot guidance: https://github.com/eitssg/simple-cloud-kit/blob/develop/.github/copilot-instructions.md
 
