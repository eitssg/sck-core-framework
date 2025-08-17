"""Time utilities for the Core Automation framework.

Provides standardized time handling functions for consistent timestamp generation
and timezone management across the framework. All timestamps use UTC timezone
to ensure consistency in distributed systems and cross-region deployments.

Key Features:
    - **UTC standardization** for timezone-aware timestamps
    - **Consistent formatting** across framework components
    - **ISO8601 compatibility** for API and logging integration
    - **Framework integration** with build tracking and event logging
"""

from datetime import datetime, timezone


def make_default_time() -> datetime:
    """Generate a UTC timezone-aware datetime for the current moment.

    Creates a standardized timestamp using UTC timezone for consistent
    time handling across different regions and environments. This function
    serves as the framework's primary time source for build tracking,
    event logging, and audit trails.

    Returns:
        Current UTC datetime with timezone information.

    Examples:
        >>> timestamp = make_default_time()
        >>> print(timestamp.tzinfo)
        datetime.timezone.utc
        >>> print(timestamp.isoformat())
        '2024-01-15T14:30:45.123456+00:00'

        >>> # Framework usage patterns
        >>> build_start_time = make_default_time()
        >>> # ... perform build operations ...
        >>> build_end_time = make_default_time()
        >>> duration = build_end_time - build_start_time

    Usage Patterns:
        Common framework integration scenarios:

        >>> # Event logging
        >>> event = {
        ...     "timestamp": make_default_time(),
        ...     "event_type": "deployment_started",
        ...     "build_id": "prn:portfolio:app:branch:1.0.0"
        ... }

        >>> # Build tracking
        >>> build_record = {
        ...     "created_at": make_default_time(),
        ...     "status": "DEPLOY_IN_PROGRESS",
        ...     "last_updated": make_default_time()
        ... }

    Notes:
        - Always returns timezone-aware datetime objects
        - Compatible with JSON serialization via framework's custom serializers
        - Provides microsecond precision for detailed timing analysis
        - Standardized across all Core Automation components
    """
    return datetime.now(timezone.utc)
