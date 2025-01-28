from typing import Any
import time
import threading
import boto3

MAX_SESSION_TIME = 3600  # 1 hour


class InsecureEnclave:
    """

    Create a secure enblave to store data in memory such as credentials, session data, and tokens

    Args:
        key: str: The key to encrypt and decrypt the data
        cipher_suite: Fernet: The cipher suite to encrypt and decrypt the data
        storage: dict[str, dict[str, Any]]: The storage to store the data
        lock: threading.Lock: The lock to prevent

    """

    storage: dict[str, Any]
    lock: threading.Lock

    def __init__(self):
        self.storage = {}
        self.lock = threading.Lock()

    def store(self, key: str, data: Any, ttl: int = MAX_SESSION_TIME) -> str:
        """
        Store the bytes provided in the storage with the key provided.  Data is encrypted with a random encrption key

        Args:
            key: str: The key to store the data
            data: bytes: The data to store
            ttl: int: The time to live for the data in seconds.  Default is 1 hour

        Returns:
            str: The key to retrieve the data (the value of the key provided)
        """
        with self.lock:
            self.storage[key] = data
        purge_thread = threading.Thread(target=self._purge_expired, args=(key, ttl))
        purge_thread.name = f"purge_expired_{key}"
        purge_thread.daemon = True
        purge_thread.start()

        return key

    def retrieve(self, key: str) -> Any | None:
        """Retrieve the data from the storage with the key provided.  Data is decrypted with the random encrption key

        If the data has expired, a None will be returned.

        Args:
            key: str: The key to retrieve the data

        Returns:
            bytes | None: The data if it exists, otherwise None

        """
        with self.lock:
            item = self.storage.get(key)
            return item

    def _purge_expired(self, key: str, ttl: int):
        """Automatically purge data fro the store after the ttl has expired"""
        time.sleep(ttl)
        with self.lock:
            if key in self.storage:
                del self.storage[key]

    def store_session(
        self, key: str, session: boto3.Session, ttl: int = MAX_SESSION_TIME
    ) -> str:
        """Store the boto3 session in the storage with the key provided

        This dies not seialize the entire object.  It does serialize the region_name, profile_name, access_key, secret_key, and token
        of the session.

        Args:
            key: str: The key to store the session data
            session: boto3.Session: The session to store
            ttl: int: The time to live for the session in seconds.  Default is 1 hour

        Returns:
            str: The key to retrieve the session data (the value of the key provided)

        """

        self.store(key, session, ttl)  # 5 minute session expiry

        return key

    def retrieve_session(self, key: str) -> boto3.Session | None:
        """
        Retrieve the boto3 session from the storage with the key provided.

        If the TTL has expired, the session will nolonger be in the store.

        Args:
            key: str: The key to retrieve the session data

        Returns:
            boto3.Session | None: The session if it exists, otherwise None

        """
        session = self.retrieve(key)
        return session if session else None

    def store_data(self, key: str, data: dict, ttl: int = MAX_SESSION_TIME) -> str:
        """
        Store a dictionary in the storage with the key provided.

        Please note that if you dictionary contains subdictionaries of objects, those objects
        must be serializable with pickle.  Else there is no way to retrieve the data.

        Args:
            key (str): The key used to store the data
            data (Any): The dictionary to be stored
            ttl (int, optional): TTL for the data. Defaults to MAX_SESSION_TIME.

        Returns:
            str: The key used to store the data (The value supplied in the parameters)
        """

        self.store(key, data, ttl)
        return key

    def retrieve_data(self, key: str) -> dict[str, Any] | None:
        """
        Retrieve the dictionary from the storage with the key provided.

        If the TTL has expired, the data will nolonger be in the store.

        Args:
            key (str): The key used to store the data

        Returns:
            dict | None: The dictionary if it exists, otherwise None
        """
        serialized_data = self.retrieve(key)
        return serialized_data if serialized_data else None
