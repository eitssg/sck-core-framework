"""Magic module for emulating boto3 S3 clients, resources, and objects.

This module allows for transparently switching between using AWS S3 and a local
filesystem for object storage, which is useful for development and testing.
"""

from typing import Any, Self, IO
import os
import shutil
import mimetypes
import hashlib
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from core_framework.common import (
    get_storage_volume,
    get_bucket_name,
    get_region,
    is_use_s3,
)

import core_helper.aws as aws


class FileStreamingBody:
    """Custom streaming body that mimics boto3's StreamingBody."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._file = None
        self._closed = False

    def read(self, amt: int = None) -> bytes:
        """Read up to amt bytes from the stream."""
        if self._closed:
            raise ValueError("I/O operation on closed file.")

        if self._file is None:
            self._file = open(self.file_path, "rb")

        try:
            return self._file.read(amt)
        except Exception:
            self.close()
            raise

    def close(self):
        """Close the file handle."""
        if self._file and not self._closed:
            self._file.close()
            self._file = None
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        """Ensure file is closed when object is garbage collected."""
        self.close()

    @property
    def closed(self) -> bool:
        """Check if the stream is closed."""
        return self._closed


class MagicObject(BaseModel):
    """Emulates an S3 Object to allow local filesystem storage via the S3 API.

    :ivar bucket_name: The name of the bucket containing the object.
    :vartype bucket_name: str
    :ivar key: The key of the object within the bucket.
    :vartype key: str | None
    :ivar data_path: The root directory for local storage.
    :vartype data_path: str
    :ivar version_id: The version ID of the object, emulated using file modification time.
    :vartype version_id: str | None
    :ivar content_type: The MIME type of the object.
    :vartype content_type: str | None
    :ivar etag: The ETag of the object, emulated using a file hash.
    :vartype etag: str | None
    :ivar error: Any error message encountered during an operation.
    :vartype error: str | None
    """

    model_config = ConfigDict(populate_by_name=True)

    bucket_name: str = Field(default_factory=get_bucket_name, alias="Bucket")
    key: str | None = Field(default=None, alias="Key")
    data_path: str = Field(default_factory=get_storage_volume, alias="DataPath")
    version_id: str | None = Field(default=None, alias="VersionId")
    content_type: str | None = Field(default=None, alias="ContentType")
    etag: str | None = Field(default=None, alias="ETag")
    error: str | None = Field(default=None, alias="Error")
    body: Any | None = Field(default=None, alias="Body")

    def head_object(self, **kwargs) -> Self:
        """Emulates the S3 head_object() API method to get object metadata.

        :param kwargs: Keyword arguments, expects 'Key'.
        :return: The instance of the object with populated metadata.
        :rtype: Self
        """
        try:
            self.key = kwargs.get("Key", self.key)
            if not self.key:
                raise ValueError("Key is required")

            fn = os.path.join(self.data_path, self.bucket_name, self.key)

            if os.path.exists(fn):
                # get the timestamp of the file
                self.version_id = str(int(os.stat(fn).st_mtime))
                self.etag = self.generate_file_hash(fn)
            else:
                self.version_id = None
                self.etag = None

            self.content_type, _ = mimetypes.guess_type(os.path.basename(self.key))

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        return self

    def generate_file_hash(self, file_path: str, hash_algorithm: str = "sha256") -> str:
        """Generates a hash of a file.

        :param file_path: The path to the file.
        :type file_path: str
        :param hash_algorithm: The hash algorithm to use (default: 'sha256').
        :type hash_algorithm: str, optional
        :return: The hexadecimal hash of the file.
        :rtype: str
        """
        hash_func = hashlib.new(hash_algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    def copy_from(self, **kwargs) -> dict:  # noqa: C901
        """Emulates the S3 copy_from() method to copy an object on the local filesystem.

        :param kwargs: Keyword arguments, expects 'CopySource'.
                       'CopySource' is a dict with 'Bucket' and 'Key'.
        :return: A dictionary emulating the S3 CopyObjectResult.
        :rtype: dict
        """
        try:
            source = kwargs.get("CopySource", None)
            if not source:
                raise ValueError("Copy source 'CopySource' is required")

            source_bucket = source.get("Bucket", None)
            source_key = source.get("Key", None)

            if not source_bucket:
                raise ValueError("Source bucket 'Bucket' is required")

            if not source_key:
                raise ValueError("Source key 'Key' is required")

            if not self.key:
                raise ValueError("Destination Bucket key has not been specified")

            if source_bucket != self.bucket_name:
                raise ValueError(f"Source S3 bucket '{source_bucket}' must be in same bucket as the target '{self.bucket_name}'")

            source_fn = os.path.join(self.data_path, source_bucket, source_key)
            target_fn = os.path.join(self.data_path, self.bucket_name, self.key)

            if source_key and self.key:
                os.makedirs(os.path.dirname(target_fn), exist_ok=True)
                shutil.copy(source_fn, target_fn)
            else:
                raise ValueError("Source and destination keys are required")

            self.head_object()

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        dt = datetime.fromtimestamp(int(self.version_id)).isoformat() if self.version_id else None

        rv = {
            "CopyObjectResult": {
                "ETag": self.etag,
                "LastModified": dt,
            },
            "VersionId": self.version_id,
            "RequestCharged": "requester",
        }
        if self.error:
            rv["Error"] = self.error

        return rv

    def download_fileobj(self, **kwargs) -> Self:
        """Emulates the S3 download_fileobj() method to download from the local filesystem.

        :param kwargs: Keyword arguments, expects 'Key' and 'Fileobj'.
        :return: The instance of the object.
        :rtype: Self
        """
        try:
            self.key = kwargs.get("Key", self.key)
            if not self.key:
                raise ValueError("Key is required")

            key = os.path.join(self.data_path, self.bucket_name, self.key)

            fileobj = kwargs.get("Fileobj")
            if fileobj is None:
                raise ValueError("Fileobj is required")

            if os.path.exists(key):
                with open(key, "rb") as file:
                    fileobj.write(file.read())
                fileobj.seek(0)

            self.head_object()

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        return self

    def put_object(self, **kwargs) -> Self:
        """Emulates the S3 put_object() method to store a file on the local filesystem.

        :param kwargs: Keyword arguments, expects 'Key' and 'Body'.
        :return: The instance of the object.
        :rtype: Self
        """
        try:
            self.key = kwargs.get("Key", self.key)
            if not self.key:
                raise ValueError("Key is required")

            body = kwargs.get("Body")
            if body is None:
                raise ValueError("Body is required")

            fn = os.path.join(self.data_path, self.bucket_name, self.key)

            dirname = os.path.dirname(fn)
            os.makedirs(dirname, exist_ok=True)

            if isinstance(body, IO):
                with open(fn, "wb") as file:
                    shutil.copyfileobj(body, file)
            elif isinstance(body, str):
                with open(fn, "w", encoding="utf-8") as file:
                    file.write(body)
            elif isinstance(body, bytes):
                with open(fn, "wb") as file:
                    file.write(body)
            else:
                raise ValueError("Body must be a file-like object, string, or bytes")

            self.head_object()

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        return self

    def get_object(self, **kwargs) -> dict:
        """Emulates the S3 get_object() method to retrieve an object from the local filesystem.

        :param kwargs: Keyword arguments, expects 'Key'.
        :return: A dictionary containing the object's metadata and body.
        :rtype: dict
        """
        try:
            self.key = kwargs.get("Key", self.key)
            if not self.key:
                raise ValueError("Key is required")

            key = os.path.join(self.data_path, self.bucket_name, self.key)

            if not os.path.exists(key):
                raise FileNotFoundError(f"Object {self.key} does not exist in bucket {self.bucket_name}")

            # the get_object method returns a stream in the Body field
            self.body = FileStreamingBody(key)

            self.head_object()

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        return self.model_dump(exclude_none=True, by_alias=True)


class MagicBucket(BaseModel):
    """Emulates an S3 Bucket to allow local filesystem storage via the S3 API.

    :ivar name: The name of the bucket.
    :vartype name: str
    :ivar data_path: The root directory for local storage.
    :vartype data_path: str | None
    """

    name: str = Field(default_factory=get_bucket_name, alias="Bucket")
    data_path: str | None = Field(default_factory=get_storage_volume, alias="DataPath")

    def head_object(self, **kwargs) -> dict:
        """Emulates the S3 head_object() method to get object metadata.

        :param kwargs: Keyword arguments passed to the MagicObject.
        :return: A dictionary of the object's metadata.
        :rtype: dict
        """
        key = kwargs.pop("Key", None)
        obj = self.Object(key)
        return obj.head_object(**kwargs).model_dump(exclude_none=True, by_alias=True)

    def download_fileobj(self, **kwargs) -> dict:
        """Emulates the S3 download_fileobj() method.

        :param kwargs: Keyword arguments passed to the MagicObject.
        :return: A dictionary of the object's metadata after download.
        :rtype: dict
        """
        key = kwargs.pop("Key", None)
        obj = self.Object(key)
        return obj.download_fileobj(**kwargs).model_dump(exclude_none=True, by_alias=True)

    def put_object(self, **kwargs) -> MagicObject:
        """Emulates the S3 put_object() method.

        :param kwargs: Keyword arguments passed to the MagicObject.
        :return: The MagicObject instance after the put operation.
        :rtype: MagicObject
        """
        key = kwargs.pop("Key", None)
        obj = self.Object(key)
        return obj.put_object(**kwargs)

    def get_object(self, **kwargs) -> dict:
        """Emulates the S3 get_object() method to retrieve an object.

        :param kwargs: Keyword arguments passed to the MagicObject.
        :return: A dictionary of the object's metadata.
        :rtype: dict
        """
        key = kwargs.pop("Key", None)
        obj = self.Object(key)
        return obj.get_object(**kwargs)

    def Object(self, key: str | None) -> MagicObject:
        """Emulates the S3 Bucket.Object() method to return a MagicObject.

        :param key: The key of the object.
        :type key: str or None
        :return: A MagicObject instance.
        :rtype: MagicObject
        """
        if self.data_path:
            return MagicObject(Bucket=self.name, Key=key, DataPath=self.data_path)
        else:
            return MagicObject(Bucket=self.name, Key=key)


class MagicS3Client(BaseModel):
    """Emulates an S3 client to allow local filesystem storage via the S3 API.

    :ivar region_name: The AWS region.
    :vartype region_name: str
    :ivar data_path: The root directory for local storage.
    :vartype data_path: str | None
    """

    region_name: str = Field(default_factory=get_region, alias="Region")
    data_path: str | None = Field(alias="DataPath", default=None)

    def head_object(self, **kwargs) -> dict:
        """Emulates the S3 client.head_object() method.

        :param kwargs: Keyword arguments, expects 'Bucket' and 'Key'.
        :return: A dictionary of the object's metadata.
        :rtype: dict
        """
        bucket_name = kwargs.pop("Bucket", None)
        bucket = self.Bucket(bucket_name)
        return bucket.head_object(**kwargs)

    def download_fileobj(self, **kwargs) -> dict:
        """Emulates the S3 client.download_fileobj() method.

        :param kwargs: Keyword arguments, expects 'Bucket', 'Key', and 'Fileobj'.
        :return: A dictionary of the object's metadata after download.
        :rtype: dict
        """
        bucket_name = kwargs.pop("Bucket", None)
        bucket = self.Bucket(bucket_name)
        return bucket.download_fileobj(**kwargs)

    def put_object(self, **kwargs) -> MagicObject:
        """Emulates the S3 client.put_object() method.

        :param kwargs: Keyword arguments, expects 'Bucket', 'Key', and 'Body'.
        :return: The MagicObject instance after the put operation.
        :rtype: MagicObject
        """
        bucket_name = kwargs.pop("Bucket", None)
        bucket = self.Bucket(bucket_name)
        return bucket.put_object(**kwargs)

    def Bucket(self, bucket_name: str) -> MagicBucket:
        """Emulates the S3 client.Bucket() method to return a MagicBucket.

        :param bucket_name: The name of the bucket.
        :type bucket_name: str
        :return: A MagicBucket instance.
        :rtype: MagicBucket
        """
        return MagicBucket(Bucket=bucket_name, DataPath=self.data_path)

    @staticmethod
    def get_bucket(Region: str, BucketName: str, RoleArn: str = None, DataPath: str | None = None) -> Any:
        """Gets a Bucket object, which can be a real S3 Bucket or a MagicBucket.

        The selection is based on the ``is_use_s3()`` configuration.

        :param Region: The AWS region of the bucket.
        :type Region: str
        :param BucketName: The name of the bucket.
        :type BucketName: str
        :param DataPath: The local storage path if not using S3. Defaults to None.
        :type DataPath: str or None, optional
        :return: An S3 Bucket or a MagicBucket instance.
        :rtype: Any
        """
        if is_use_s3():
            s3 = aws.s3_resource(region=Region, role_arn=RoleArn)
            bucket = s3.Bucket(BucketName)
        else:
            local = MagicS3Client(Region=Region, DataPath=DataPath)
            bucket = local.Bucket(BucketName)

        return bucket

    @staticmethod
    def get_client(Region: str, RoleArn: str = None, DataPath: str | None = None) -> Any:
        """Gets an S3 client, which can be a real boto3 client or a MagicS3Client.

        The selection is based on the ``is_use_s3()`` configuration.

        :param Region: The AWS region for the client.
        :type Region: str
        :param RoleArn: The ARN of the role to assume for the client. Defaults to None.
        :type RoleArn: str or None, optional
        :param DataPath: The local storage path if not using S3. Defaults to None.
        :type DataPath: str or None, optional
        :return: A boto3 S3 client or a MagicS3Client instance.
        :rtype: Any
        """
        if is_use_s3():
            client = aws.s3_client(region=Region, role_arn=RoleArn)
        else:
            client = MagicS3Client(Region=Region, DataPath=DataPath)

        return client


class SeekableStreamWrapper:
    """Wrapper that makes a streaming body seekable by buffering chunks."""

    def __init__(self, stream, chunk_size: int = 8192):
        self.stream = stream
        self.chunk_size = chunk_size
        self.buffer = bytearray()
        self.position = 0
        self.eof_reached = False

    def read(self, size: int = -1) -> bytes:
        # Ensure we have enough data buffered
        if size == -1:
            self._read_all()
            result = bytes(self.buffer[self.position :])
            self.position = len(self.buffer)
        else:
            self._ensure_buffered(self.position + size)
            end_pos = min(self.position + size, len(self.buffer))
            result = bytes(self.buffer[self.position : end_pos])
            self.position = end_pos

        return result

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:  # SEEK_SET
            self.position = offset
        elif whence == 1:  # SEEK_CUR
            self.position += offset
        elif whence == 2:  # SEEK_END
            self._read_all()
            self.position = len(self.buffer) + offset

        self.position = max(0, min(self.position, len(self.buffer)))
        return self.position

    def _ensure_buffered(self, target_size: int):
        while len(self.buffer) < target_size and not self.eof_reached:
            chunk = self.stream.read(self.chunk_size)
            if not chunk:
                self.eof_reached = True
                break
            self.buffer.extend(chunk)

    def _read_all(self):
        while not self.eof_reached:
            chunk = self.stream.read(self.chunk_size)
            if not chunk:
                self.eof_reached = True
                break
            self.buffer.extend(chunk)
