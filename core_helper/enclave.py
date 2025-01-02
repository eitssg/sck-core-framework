from typing import Any
import time
import threading
from cryptography.fernet import Fernet
import boto3
import pickle

import core_framework as util

MAX_SESSION_TIME = 3600  # 1 hour


class SecureEnclave:
    """

    Create a secure enblave to store data in memory such as credentials, session data, and tokens

    Args:
        key: str: The key to encrypt and decrypt the data
        cipher_suite: Fernet: The cipher suite to encrypt and decrypt the data
        storage: dict[str, dict[str, Any]]: The storage to store the data
        lock: threading.Lock: The lock to prevent

    """

    key: str
    cipher_suite: Fernet
    storage: dict[str, Any]
    lock: threading.Lock

    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        self.storage = {}
        self.lock = threading.Lock()

    def store(self, key: str, data: bytes, ttl: int = MAX_SESSION_TIME) -> str:
        """
        Store the bytes provided in the storage with the key provided.  Data is encrypted with a random encrption key

        Args:
            key: str: The key to store the data
            data: bytes: The data to store
            ttl: int: The time to live for the data in seconds.  Default is 1 hour

        Returns:
            str: The key to retrieve the data (the value of the key provided)
        """
        encrypted_data = self.cipher_suite.encrypt(data)
        with self.lock:
            self.storage[key] = encrypted_data
        threading.Thread(target=self._purge_expired, args=(key, ttl)).start()

        return key

    def retrieve(self, key: str) -> bytes | None:
        """Retrieve the data from the storage with the key provided.  Data is decrypted with the random encrption key

        If the data has expired, a None will be returned.

        Args:
            key: str: The key to retrieve the data

        Returns:
            bytes | None: The data if it exists, otherwise None

        """
        with self.lock:
            item = self.storage.get(key)
            return self.cipher_suite.decrypt(item) if item else None

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
        session_data = {
            "region_name": session.region_name,
            "profile_name": session.profile_name,
        }

        credentials = session.get_credentials()
        if credentials is not None:
            session_data.update(
                {
                    "access_key": credentials.access_key,
                    "secret_key": credentials.secret_key,
                }
            )
            if credentials.token is not None:
                session_data["token"] = credentials.token

        self.store(key, pickle.dumps(session_data), ttl)  # 5 minute session expiry

        return key

    def __create_session(self, data: dict) -> boto3.Session:
        """Create a boto3 session from the data provided

        Args:
            data: dict: The data to create the boto3 session. Creditentials and region, etc.

        """
        region_name = data.get("region_name", util.get_region())
        profile_name = data.get("profile_name", util.get_aws_profile())

        access_key = data.get("access_key", None)
        secret_key = data.get("secret_key", None)

        token = data.get("token", None)

        if not access_key or not secret_key:
            return boto3.Session(region_name=region_name, profile_name=profile_name)

        if not token:
            return boto3.Session(
                region_name=region_name,
                profile_name=profile_name,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )

        return boto3.Session(
            region_name=region_name,
            profile_name=profile_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=token,
        )

    def retrieve_session(self, key: str) -> boto3.Session | None:
        """
        Retrieve the boto3 session from the storage with the key provided.

        If the TTL has expired, the session will nolonger be in the store.

        Args:
            key: str: The key to retrieve the session data

        Returns:
            boto3.Session | None: The session if it exists, otherwise None

        """
        session_data = self.retrieve(key)

        return (
            self.__create_session(pickle.loads(session_data)) if session_data else None
        )

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

        serialized_data = pickle.dumps(data)
        self.store(key, serialized_data, ttl)
        return key

    def retrieve_data(self, key: str) -> dict | None:
        """
        Retrieve the dictionary from the storage with the key provided.

        If the TTL has expired, the data will nolonger be in the store.

        Args:
            key (str): The key used to store the data

        Returns:
            dict | None: The dictionary if it exists, otherwise None
        """
        serialized_data = self.retrieve(key)
        return pickle.loads(serialized_data) if serialized_data else None
