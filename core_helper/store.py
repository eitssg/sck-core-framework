from .cache import InMemoryCache

# This cache is instantiated at the module level, so it persists across
# Lambda invocations within the same execution environment.
store = InMemoryCache()
