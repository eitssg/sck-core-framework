"""Thread-safe In-Memory Cache with Sliding TTL for AWS Session Management.

This module provides a high-performance, thread-safe caching system designed specifically
for AWS session and credential management within the Core Automation framework. It implements
a sliding Time-To-Live (TTL) mechanism where cached items have their expiration reset each
time they are accessed, ensuring frequently used items remain available.

Key Features:
    - **Thread Safety**: Full thread-safe operations with proper locking mechanisms
    - **Sliding TTL**: Automatic expiration extension on access to keep active items fresh
    - **Background Cleanup**: Daemon thread for automatic expired item removal
    - **AWS Integration**: Specialized methods for Boto3 session and credential caching
    - **Lambda Optimized**: Default TTL aligned with AWS Lambda execution limits
    - **Memory Efficient**: Automatic cleanup prevents memory leaks in long-running processes

Architecture:
    The cache operates with a background daemon thread that periodically scans for and
    removes expired items. This approach ensures minimal performance impact during
    cache operations while maintaining memory efficiency over time.

Use Cases:
    - Caching Boto3 sessions across Lambda invocations
    - Storing temporary AWS credentials with automatic expiration
    - Session management in multi-threaded applications
    - Performance optimization for repeated AWS API calls

Thread Safety:
    All operations are protected by threading locks to ensure safe concurrent access
    from multiple threads or Lambda execution contexts.

Constants:
    DEFAULT_TTL (int): Default cache item TTL of 900 seconds (15 minutes), matching
                      AWS Lambda's maximum execution timeout.
"""

from typing import Any, Dict, Tuple
import time
import threading
import boto3

# Default TTL for cached items, in seconds (15 minutes, the max Lambda timeout)
DEFAULT_TTL = 900


class InMemoryCache:
    """Thread-safe in-memory cache with sliding Time-To-Live (TTL) functionality.

    Provides a dictionary-like storage mechanism safe for concurrent access across
    multiple threads. Implements sliding TTL where item expiration timers reset
    on each access, keeping frequently used items available longer. A persistent
    background daemon thread handles automatic cleanup of expired items.

    The cache is optimized for AWS session and credential management but can store
    any Python object. All operations are thread-safe and designed for high
    performance in Lambda and multi-threaded environments.

    Attributes:
        _storage: Internal dictionary storing (data, expiration_timestamp) tuples
        _lock: Threading lock for synchronizing access to storage
        _cleanup_interval: Seconds between background cleanup cycles
        _stop_event: Event for graceful background thread termination
        _purge_thread: Background daemon thread for expired item removal

    Thread Safety:
        All public methods use proper locking to ensure thread-safe operations.
        The background cleanup thread operates independently with its own locking.
    """

    def __init__(self, cleanup_interval: int = 15):
        """Initialize the cache and start the background cleanup thread.

        Creates an empty cache and launches a daemon thread for periodic cleanup
        of expired items. The cleanup thread runs for the lifetime of the cache
        instance unless explicitly stopped.

        Args:
            cleanup_interval: Seconds between background cleanup cycles. Lower values
                            provide more responsive cleanup but use more CPU. Higher
                            values are more efficient but may allow expired items
                            to persist longer.

        Notes:
            The background thread is created as a daemon thread, so it will not
            prevent the Python process from exiting. Call stop() for graceful
            shutdown if needed.
        """
        # Storage format: {key: (data, expiration_timestamp)}
        self._storage: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = cleanup_interval
        self._stop_event = threading.Event()

        # Start the single, persistent background cleanup thread
        self._purge_thread = threading.Thread(target=self._purge_expired_items)
        self._purge_thread.daemon = True
        self._purge_thread.start()

    def store(self, key: str, data: Any, ttl: int = DEFAULT_TTL) -> None:
        """Store or update an item in the cache with specified TTL.

        Adds a new item to the cache or updates an existing item with new data
        and expiration time. The TTL countdown begins immediately upon storage.

        Args:
            key: Unique identifier for the cached item. If the key already exists,
                its value and expiration will be completely replaced.
            data: Python object to cache. Can be any type as this is in-memory
                 storage with no serialization requirements.
            ttl: Time-To-Live in seconds. The item will expire after this duration
                unless accessed via retrieve(), which resets the timer.

        Thread Safety:
            This method is thread-safe and can be called concurrently from
            multiple threads without data corruption.
        """
        with self._lock:
            expiration = time.time() + ttl
            self._storage[key] = (data, expiration)

    def retrieve(self, key: str, ttl: int = DEFAULT_TTL) -> Any | None:
        """Retrieve an item from cache and reset its TTL (sliding expiration).

        Implements sliding TTL behavior where successful retrieval extends the
        item's lifetime. If the item exists and hasn't expired, its expiration
        timer is reset to the current time plus the provided TTL.

        Args:
            key: The identifier of the item to retrieve.
            ttl: New TTL in seconds to set for the item if successfully retrieved.
                This implements the "sliding" behavior where active items stay
                cached longer.

        Returns:
            The cached data if the key exists and hasn't expired, otherwise None.
            Expired items are automatically removed during retrieval.

        Behavior:
            - Non-existent key: Returns None
            - Expired item: Removes from cache and returns None
            - Valid item: Resets expiration timer and returns data

        Thread Safety:
            This method is thread-safe and handles expiration checking and TTL
            reset atomically under a single lock.
        """
        with self._lock:
            item = self._storage.get(key)
            if item is None:
                return None  # Item does not exist

            data, expiration = item
            current_time = time.time()

            if current_time > expiration:
                # Item has expired, remove it and return None
                del self._storage[key]
                return None
            else:
                # Item is valid, reset its TTL and return the data
                new_expiration = current_time + ttl
                self._storage[key] = (data, new_expiration)
                return data

    def _purge_expired_items(self) -> None:
        """Background task for periodic removal of expired cache items.

        Runs continuously in a daemon thread, waking at intervals defined by
        cleanup_interval to scan the cache for expired items and remove them.
        This prevents memory leaks in long-running processes.

        Algorithm:
            1. Sleep for cleanup_interval seconds
            2. Scan all items for expiration (under lock)
            3. Remove expired items (under lock)
            4. Repeat until stop_event is set

        Thread Safety:
            Uses the same lock as other methods to ensure atomic operations
            during cleanup. Minimizes lock time by collecting expired keys
            before removal.

        Notes:
            This method is private and should not be called directly. It runs
            automatically in the background thread started during initialization.
        """
        while not self._stop_event.is_set():
            expired_keys = []
            current_time = time.time()
            # It's safer to lock only when modifying the dictionary
            with self._lock:
                for key, (_, expiration) in self._storage.items():
                    if current_time > expiration:
                        expired_keys.append(key)

                for key in expired_keys:
                    # Ensure the key still exists before deleting
                    if key in self._storage:
                        del self._storage[key]

            # Wait for the next cleanup interval
            time.sleep(self._cleanup_interval)

    def stop(self) -> None:
        """Stop the background cleanup thread gracefully.

        Signals the background cleanup thread to terminate and waits for it
        to finish. Should be called before application exit to ensure proper
        resource cleanup and thread termination.

        Behavior:
            1. Sets the stop event to signal thread termination
            2. Waits for the background thread to complete
            3. After this call, no more automatic cleanup will occur

        Notes:
            Once stopped, the cache will continue to function for storage and
            retrieval operations, but expired items will only be removed during
            explicit retrieve() calls, not automatically in the background.
        """
        self._stop_event.set()
        self._purge_thread.join()

    def store_session(
        self, key: str, session: boto3.Session, ttl: int = DEFAULT_TTL
    ) -> str:
        """Store a Boto3 Session object in the cache with type safety.

        Provides a type-safe wrapper around the generic store() method specifically
        for caching Boto3 sessions. Sessions are stored as complete objects with
        all their configuration and credential information.

        Args:
            key: Unique identifier for the session. Typically combines profile
                and region information for uniqueness.
            session: The Boto3 Session object to cache. This includes region,
                   profile, and credential configuration.
            ttl: Time-To-Live in seconds for the cached session.

        Returns:
            The same key that was passed in, useful for method chaining or
            confirmation of storage.

        Use Cases:
            - Caching authenticated sessions across Lambda invocations
            - Reusing configured sessions in multi-threaded applications
            - Performance optimization for repeated AWS API access
        """
        self.store(key, session, ttl)
        return key

    def retrieve_session(self, key: str) -> boto3.Session | None:
        """Retrieve a Boto3 Session from cache with automatic TTL extension.

        Provides type-safe retrieval of cached Boto3 sessions with sliding TTL
        behavior. Successfully retrieved sessions have their expiration reset
        to maintain availability for active use.

        Args:
            key: The identifier used when storing the session.

        Returns:
            The cached Boto3 Session if it exists and hasn't expired, otherwise
            None. The session is returned as a fully configured object ready
            for immediate use.

        Behavior:
            - Valid session: Returns session object and resets TTL
            - Expired/missing session: Returns None
            - TTL is reset using DEFAULT_TTL on successful retrieval

        Thread Safety:
            Session retrieval is thread-safe and atomic with TTL reset operations.
        """
        session = self.retrieve(key)
        return session if session else None

    def store_data(self, key: str, data: dict, ttl: int = DEFAULT_TTL) -> str:
        """Store a dictionary in the cache with type hints for IDE support.

        Provides a type-safe wrapper around the generic store() method specifically
        for caching dictionary data. Commonly used for AWS credentials, configuration
        data, and API responses.

        Args:
            key: Unique identifier for the cached data.
            data: Dictionary to cache. While typed as dict, any Python object
                 can actually be stored due to in-memory storage.
            ttl: Time-To-Live in seconds for the cached data.

        Returns:
            The same key that was passed in, confirming successful storage.

        Common Use Cases:
            - Caching AWS temporary credentials
            - Storing API response data
            - Caching configuration dictionaries
            - Temporary storage of computed results
        """
        self.store(key, data, ttl)
        return key

    def retrieve_data(self, key: str) -> dict[str, Any] | None:
        """Retrieve a dictionary from cache with automatic TTL extension.

        Provides type-safe retrieval of cached dictionary data with sliding TTL
        behavior. Successfully retrieved data has its expiration reset to maintain
        availability for continued use.

        Args:
            key: The identifier used when storing the data.

        Returns:
            The cached dictionary if it exists and hasn't expired, otherwise None.
            The return type suggests dict[str, Any] but the actual returned object
            depends on what was originally stored.

        Behavior:
            - Valid data: Returns data object and resets TTL using DEFAULT_TTL
            - Expired/missing data: Returns None
            - TTL extension helps keep frequently accessed data available

        Thread Safety:
            Data retrieval is thread-safe and atomic with TTL reset operations.
        """
        data = self.retrieve(key)
        return data if data else None

    def clear_data(self, key: str) -> None:
        """Remove a specific item from the cache immediately.

        Provides explicit removal of cached items regardless of their expiration
        status. Useful for cache invalidation, cleanup, or removing sensitive
        data when no longer needed.

        Args:
            key: The identifier of the item to remove from cache.

        Behavior:
            - Existing item: Removed immediately from cache
            - Non-existent item: No effect, no error raised
            - Removal is permanent and immediate

        Thread Safety:
            This method is thread-safe and ensures atomic removal operations
            even during concurrent access from other threads.

        Use Cases:
            - Invalidating cached credentials after role changes
            - Forced cleanup of sensitive data
            - Manual cache management and optimization
            - Error recovery by clearing potentially corrupted cache entries
        """
        with self._lock:
            if key in self._storage:
                del self._storage[key]
