from typing import Any, Dict, Tuple
import time
import threading
import boto3

# Default TTL for cached items, in seconds (15 minutes, the max Lambda timeout)
DEFAULT_TTL = 900


class InMemoryCache:
    """
    A simple, thread-safe, in-memory cache with a sliding Time-To-Live (TTL).

    This class provides a dictionary-like storage mechanism that is safe for use
    across multiple threads. It implements a "sliding" TTL, where an item's
    expiration timer is reset every time it is accessed via the `retrieve`
    method. A single, persistent background thread handles the periodic removal
    of items that have expired due to inactivity.
    """

    def __init__(self, cleanup_interval: int = 15):
        """
        Initializes the cache and starts the background cleanup thread.

        :param cleanup_interval: The interval, in seconds, at which the background
                                 thread should wake up to purge expired items from
                                 the cache.
        :type cleanup_interval: int
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
        """
        Stores or updates an item in the cache with a specific TTL.

        If the key already exists, its value and expiration time will be
        overwritten with the new data and TTL.

        :param key: The unique key to associate with the data.
        :type key: str
        :param data: The Python object to be stored in the cache.
        :type data: Any
        :param ttl: The Time-To-Live for the item, in seconds. The item will be
                    considered expired if it is not accessed within this duration.
        :type ttl: int
        """
        with self._lock:
            expiration = time.time() + ttl
            self._storage[key] = (data, expiration)

    def retrieve(self, key: str, ttl: int = DEFAULT_TTL) -> Any | None:
        """
        Retrieves an item from the cache and resets its TTL.

        If the item is found and has not expired, its expiration timer is "reset"
        to the current time plus the provided TTL, effectively extending its life.
        If the item does not exist or has already expired, it is removed from the
        cache and this method returns None.

        :param key: The key of the item to retrieve.
        :type key: str
        :param ttl: The new TTL to set for the item if it is successfully retrieved,
                    extending its lifetime.
        :type ttl: int
        :return: The cached data if the key exists and the item is not expired,
                 otherwise None.
        :rtype: Any | None
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
        """
        A background task that periodically removes all expired items.

        This method runs in a dedicated daemon thread. It wakes up at intervals
        defined by `cleanup_interval`, scans the entire cache for items whose
        expiration timestamp is in the past, and removes them.
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
        """
        Stops the background cleanup thread gracefully.

        This method should be called before the application exits to ensure
        the background thread is properly joined and resources are released.
        """
        self._stop_event.set()
        self._purge_thread.join()

    def store_session(
        self, key: str, session: boto3.Session, ttl: int = DEFAULT_TTL
    ) -> str:
        """
        Stores a Boto3 Session object in the cache.

        This method acts as a convenient wrapper around the generic `store`
        method for the specific use case of caching Boto3 sessions. The entire
        session object is stored in memory.

        :param key: The key to associate with the Boto3 session.
        :type key: str
        :param session: The Boto3 Session object to be cached.
        :type session: boto3.Session
        :param ttl: The time to live for the session in seconds.
        :type ttl: int
        :return: The key used to store the session, which is the same value
                 passed in the `key` parameter.
        :rtype: str
        """
        self.store(key, session, ttl)
        return key

    def retrieve_session(self, key: str) -> boto3.Session | None:
        """
        Retrieves a Boto3 Session object from the cache.

        If the session has expired or was never stored, this method returns None.
        Accessing a valid session will reset its time-to-live.

        :param key: The key used to store the session.
        :type key: str
        :return: The cached Boto3 Session object, or None if it does not exist
                 or has expired.
        :rtype: boto3.Session | None
        """
        session = self.retrieve(key)
        return session if session else None

    def store_data(self, key: str, data: dict, ttl: int = DEFAULT_TTL) -> str:
        """
        Stores a dictionary in the cache.

        This is a wrapper around the generic `store` method, specifically typed
        for storing dictionaries. Any Python object can be stored, as this is an
        in-memory cache and does not perform serialization.

        :param key: The key to associate with the data.
        :type key: str
        :param data: The dictionary to be stored.
        :type data: dict
        :param ttl: The time to live for the data in seconds.
        :type ttl: int
        :return: The key used to store the data.
        :rtype: str
        """
        self.store(key, data, ttl)
        return key

    def retrieve_data(self, key: str) -> dict[str, Any] | None:
        """
        Retrieves a dictionary from the cache.

        If the data has expired or was never stored, this method returns None.
        Accessing valid data will reset its time-to-live.

        :param key: The key used to store the data.
        :type key: str
        :return: The cached dictionary, or None if it does not exist or has expired.
        :rtype: dict[str, Any] | None
        """
        data = self.retrieve(key)
        return data if data else None

    def clear_data(self, key: str) -> None:
        """
        Clears a specific item from the cache.

        This method removes the item associated with the given key from the cache,
        regardless of its expiration status.

        :param key: The key of the item to be removed.
        :type key: str
        """
        with self._lock:
            if key in self._storage:
                del self._storage[key]
