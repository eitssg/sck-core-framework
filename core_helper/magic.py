"""Magic module for emulating boto3 S3 clients, resources, and objects.

This module provides transparent switching between AWS S3 and local filesystem storage,
enabling seamless development and testing without requiring actual S3 infrastructure.
It implements drop-in replacements for boto3 S3 functionality that store data locally
while maintaining API compatibility.

Key Features:
    - **API Compatibility**: Drop-in replacement for boto3 S3 operations
    - **Local Storage**: Uses filesystem instead of S3 for development/testing
    - **Transparent Switching**: Automatic selection based on configuration
    - **Streaming Support**: Emulates boto3 StreamingBody with file-like interface
    - **Metadata Emulation**: Generates ETag, version ID, and content type locally
    - **Error Handling**: Consistent error responses matching S3 behavior

Components:
    - **FileStreamingBody**: Emulates boto3's StreamingBody for file reading
    - **MagicObject**: Emulates S3 Object with filesystem operations
    - **MagicBucket**: Emulates S3 Bucket with object management
    - **MagicS3Client**: Emulates S3 Client with bucket operations
    - **SeekableStreamWrapper**: Adds seek functionality to streaming bodies

Configuration:
    The module uses core_framework configuration to determine whether to use
    real S3 or local filesystem storage via the is_use_s3() function.

Integration:
    Designed to work seamlessly with the Core Automation framework's storage
    patterns and configuration management system.
"""

from typing import Any, Self

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
    """Custom streaming body that mimics boto3's StreamingBody for local files.

    Provides a file-like interface for reading files with proper resource management
    and context manager support. Used as a replacement for boto3's StreamingBody
    when using local filesystem storage instead of S3.

    The class implements lazy file opening and automatic resource cleanup to match
    boto3's streaming behavior while working with local files.

    Attributes:
        file_path: Path to the local file being streamed.
        _file: Internal file handle (opened lazily).
        _closed: Flag indicating if the stream has been closed.
    """

    def __init__(self, file_path: str):
        """Initialize the streaming body with a file path.

        Args:
            file_path: Path to the file to be streamed. The file is not opened
                      until the first read() call for efficiency.
        """
        self.file_path = file_path
        self._file = None
        self._closed = False

    def read(self, amt: int = None) -> bytes:
        """Read up to amt bytes from the stream.

        Opens the file lazily on first read and reads the requested amount
        of data. Handles file opening errors and ensures proper cleanup.

        Args:
            amt: Maximum number of bytes to read. If None, reads the entire file.

        Returns:
            The bytes read from the file.

        Raises:
            ValueError: If the stream is closed.
            IOError: If the file cannot be opened or read.
        """
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
        """Close the file handle and release resources.

        Once closed, the stream cannot be used for further operations.
        This method is idempotent and safe to call multiple times.
        """
        if self._file and not self._closed:
            self._file.close()
            self._file = None
            self._closed = True

    def __enter__(self):
        """Enter the context manager.

        Returns:
            Self for use in with statements.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and close the file.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        self.close()

    def __del__(self):
        """Ensure file is closed when object is garbage collected."""
        self.close()

    @property
    def closed(self) -> bool:
        """Check if the stream is closed.

        Returns:
            True if the stream is closed, False otherwise.
        """
        return self._closed


class MagicObject(BaseModel):
    """Emulates an S3 Object to allow local filesystem storage via the S3 API.

    Provides a complete implementation of S3 object operations using local filesystem
    storage. Maintains API compatibility with boto3 S3 objects while storing data
    locally for development and testing scenarios.

    The class generates metadata like ETags and version IDs using file system
    properties to emulate S3 behavior as closely as possible.

    Attributes:
        bucket_name: The name of the bucket containing the object.
        key: The key (path) of the object within the bucket.
        data_path: The root directory for local storage.
        version_id: Emulated version ID using file modification time.
        content_type: MIME type of the object determined from file extension.
        etag: Emulated ETag using file hash.
        error: Any error message encountered during operations.
        body: The object body content for streaming operations.
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
        """Emulate the S3 head_object() API method to get object metadata.

        Retrieves metadata for an object without downloading the object content.
        Populates version_id, etag, and content_type attributes based on local
        file properties.

        Args:
            **kwargs: Keyword arguments.
                Key (str): The key of the object to get metadata for.

        Returns:
            Self with populated metadata attributes.

        Notes:
            - Version ID is generated from file modification timestamp
            - ETag is generated using SHA256 hash of file content
            - Content type is determined from file extension
            - Missing files result in None values for version_id and etag
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
        """Generate a hash of a file for ETag emulation.

        Reads the file in chunks to efficiently compute hash for large files,
        providing an ETag-like identifier for local files.

        Args:
            file_path: The path to the file to hash.
            hash_algorithm: The hash algorithm to use. Defaults to 'sha256'.

        Returns:
            The hexadecimal hash of the file content.

        Raises:
            IOError: If the file cannot be read.
            ValueError: If the hash algorithm is not supported.
        """
        hash_func = hashlib.new(hash_algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    def copy_from(self, **kwargs) -> dict:
        """Emulate the S3 copy_from() method to copy an object locally.

        Copies an object from one location to another within the same bucket
        using filesystem operations. Maintains S3 API compatibility for
        copy operations.

        Args:
            **kwargs: Keyword arguments.
                CopySource (dict): Dictionary containing source bucket and key.
                    Bucket (str): The source bucket name.
                    Key (str): The source object key.

        Returns:
            A dictionary emulating the S3 CopyObjectResult with ETag,
            LastModified timestamp, and VersionId.

        Raises:
            ValueError: If required parameters are missing or invalid.
            FileNotFoundError: If the source file doesn't exist.
            OSError: If the file copy operation fails.

        Notes:
            - Source and destination must be in the same bucket
            - Creates target directory structure as needed
            - Updates object metadata after successful copy
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
                raise ValueError(
                    f"Source S3 bucket '{source_bucket}' must be in same bucket as the target '{self.bucket_name}'"
                )

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

        dt = (
            datetime.fromtimestamp(int(self.version_id)).isoformat()
            if self.version_id
            else None
        )

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
        """Emulate the S3 download_fileobj() method using local filesystem.

        Downloads object content to a file-like object by reading from the
        local filesystem and writing to the provided file object.

        Args:
            **kwargs: Keyword arguments.
                Key (str): The key of the object to download.
                Fileobj (IO): File-like object to write the downloaded content to.

        Returns:
            Self with updated metadata after the download operation.

        Raises:
            ValueError: If Key or Fileobj is missing.
            FileNotFoundError: If the local file doesn't exist.
            IOError: If file reading or writing fails.

        Notes:
            - Resets fileobj position to 0 after writing
            - Updates object metadata after successful download
            - Supports any file-like object with write() method
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
        """Emulate the S3 put_object() method using local filesystem storage.

        Stores content to the local filesystem, supporting multiple input types:
        file paths, file-like objects, strings, and bytes. Creates directory
        structure as needed and handles various content formats.

        Args:
            **kwargs: Keyword arguments for the put operation.
                Key (str): The key (path) of the object within the bucket.
                Body (IO | str | bytes): The content to store.
                Filename (str): Alternative to Body - path to a local file to upload.

        Returns:
            Self with updated metadata after the put operation.

        Raises:
            ValueError: If Key is missing, or if Body type is unsupported.
            IOError: If file operations fail.
            OSError: If directory creation fails.

        Notes:
            - Supports file-like objects, strings, bytes, and file paths
            - Creates target directory structure automatically
            - Preserves file metadata when using Filename parameter
            - Automatically closes file-like objects after processing
            - Updates object metadata after successful storage
        """
        try:
            self.key = kwargs.get("Key", self.key)
            if not self.key:
                raise ValueError("Key is required")

            # Check for Filename parameter (used by MagicBucket)
            filename = kwargs.get("Filename")
            if filename:
                # Direct file copy for Filename parameter
                fn = os.path.join(self.data_path, self.bucket_name, self.key)
                dirname = os.path.dirname(fn)
                os.makedirs(dirname, exist_ok=True)
                shutil.copy2(filename, fn)  # Preserves metadata
                self.head_object()
                return self

            body = kwargs.get("Body")
            if body is None:
                raise ValueError("Either Body or Filename is required")

            fn = os.path.join(self.data_path, self.bucket_name, self.key)
            dirname = os.path.dirname(fn)
            os.makedirs(dirname, exist_ok=True)

            # Check for file-like objects using hasattr instead of isinstance
            if hasattr(body, "read") and hasattr(body, "seek"):
                # File-like object (includes BufferedReader, IO streams, etc.)
                try:
                    with open(fn, "wb") as file:
                        shutil.copyfileobj(body, file)
                finally:
                    # Safely close the body if it has a close method
                    if hasattr(body, "close"):
                        body.close()
            elif isinstance(body, str):
                # String content
                with open(fn, "w", encoding="utf-8") as file:
                    file.write(body)
            elif isinstance(body, bytes):
                # Binary content
                with open(fn, "wb") as file:
                    file.write(body)
            else:
                raise ValueError("Body must be a file-like object, string, or bytes")

            self.head_object()

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        return self

    def get_object(self, **kwargs) -> dict:
        """Emulate the S3 get_object() method using local filesystem.

        Retrieves object content and metadata, returning a streaming body for
        the content similar to boto3's S3 get_object response format.

        Args:
            **kwargs: Keyword arguments.
                Key (str): The key of the object to retrieve.

        Returns:
            A dictionary containing the object's metadata and a streaming body,
            formatted to match S3's get_object response structure.

        Raises:
            ValueError: If Key is missing.
            FileNotFoundError: If the object doesn't exist.

        Notes:
            - Returns a FileStreamingBody in the 'Body' field
            - Includes all object metadata (ETag, ContentType, etc.)
            - Maintains S3 API response format compatibility
            - Streaming body supports context manager usage
        """
        try:
            self.key = kwargs.get("Key", self.key)
            if not self.key:
                raise ValueError("Key is required")

            key = os.path.join(self.data_path, self.bucket_name, self.key)

            if not os.path.exists(key):
                raise FileNotFoundError(
                    f"Object {self.key} does not exist in bucket {self.bucket_name}"
                )

            # the get_object method returns a stream in the Body field
            self.body = FileStreamingBody(key)

            self.head_object()

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        return self.model_dump(exclude_none=True, by_alias=True)

    def delete_object(self, **kwargs) -> Self:
        """Emulate the S3 delete_object() method using local filesystem.

        Removes the object file from the local filesystem and clears metadata
        to simulate S3 object deletion behavior.

        Args:
            **kwargs: Keyword arguments.
                Key (str): The key of the object to delete.

        Returns:
            Self after deletion with cleared metadata.

        Raises:
            ValueError: If Key is missing.
            FileNotFoundError: If the object doesn't exist.
            OSError: If file deletion fails due to permissions or other issues.

        Notes:
            - Clears version_id and etag after successful deletion
            - Raises FileNotFoundError for non-existent objects
            - Only removes the file, not empty parent directories
        """
        try:
            self.key = kwargs.get("Key", self.key)
            if not self.key:
                raise ValueError("Key is required")

            key = os.path.join(self.data_path, self.bucket_name, self.key)

            if os.path.exists(key):
                os.remove(key)
                self.version_id = None
                self.etag = None
            else:
                raise FileNotFoundError(
                    f"Object {self.key} does not exist in bucket {self.bucket_name}"
                )

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        return self


class MagicBucket(BaseModel):
    """Emulate an S3 Bucket to allow local filesystem storage via the S3 API.

    Provides bucket-level operations that delegate to MagicObject instances
    for individual object operations. Maintains API compatibility with boto3
    S3 bucket resources while using local filesystem storage.

    Acts as a factory for MagicObject instances and provides bucket-level
    operations like object listing, creation, and management.

    Attributes:
        name: The name of the bucket.
        data_path: The root directory for local storage.
    """

    name: str = Field(default_factory=get_bucket_name, alias="Bucket")
    data_path: str | None = Field(default_factory=get_storage_volume, alias="DataPath")

    def head_object(self, **kwargs) -> dict:
        """Emulate the S3 head_object() method at bucket level.

        Delegates to a MagicObject to get object metadata, providing
        bucket-level access to object metadata operations.

        Args:
            **kwargs: Keyword arguments.
                Key (str): The key of the object to get metadata for.

        Returns:
            A dictionary of the object's metadata in S3 format.
        """
        key = kwargs.pop("Key", None)
        obj = self.Object(key)
        return obj.head_object(**kwargs).model_dump(exclude_none=True, by_alias=True)

    def download_fileobj(self, **kwargs) -> dict:
        """Emulate the S3 download_fileobj() method at bucket level.

        Delegates to a MagicObject to download object content to a file-like object.

        Args:
            **kwargs: Keyword arguments.
                Key (str): The key of the object to download.
                Fileobj (IO): File-like object to write the downloaded content to.

        Returns:
            A dictionary of the object's metadata after download.
        """
        key = kwargs.pop("Key", None)
        obj = self.Object(key)
        return obj.download_fileobj(**kwargs).model_dump(
            exclude_none=True, by_alias=True
        )

    def put_object(self, **kwargs) -> MagicObject:
        """Emulate the S3 put_object() method at bucket level.

        Delegates to a MagicObject to store object content, providing
        bucket-level access to object storage operations.

        Args:
            **kwargs: Keyword arguments.
                Key (str): The key (path) of the object within the bucket.
                Body (IO | str | bytes): The content to store.
                Filename (str): Alternative to Body - path to a local file to upload.

        Returns:
            The MagicObject instance after the put operation.

        Raises:
            ValueError: If required parameters are missing or Body type is unsupported.
        """
        key = kwargs.pop("Key", None)
        obj = self.Object(key)
        return obj.put_object(**kwargs)

    def get_object(self, **kwargs) -> dict:
        """Emulate the S3 get_object() method at bucket level.

        Delegates to a MagicObject to retrieve object content and metadata.

        Args:
            **kwargs: Keyword arguments.
                Key (str): The key of the object to retrieve.

        Returns:
            A dictionary of the object's metadata and streaming body.
        """
        key = kwargs.pop("Key", None)
        obj = self.Object(key)
        return obj.get_object(**kwargs)

    def delete_object(self, **kwargs) -> dict:
        """Emulate the S3 delete_object() method at bucket level.

        Delegates to a MagicObject to delete an object from storage.

        Args:
            **kwargs: Keyword arguments.
                Key (str): The key of the object to delete.

        Returns:
            A dictionary indicating the result of the delete operation.
        """
        key = kwargs.pop("Key", None)
        obj = self.Object(key)
        return obj.delete_object(**kwargs).model_dump(exclude_none=True, by_alias=True)

    def Object(self, key: str | None) -> MagicObject:
        """Create a MagicObject instance for the specified key.

        Emulates the S3 Bucket.Object() method to return a MagicObject
        configured for this bucket and the specified key.

        Args:
            key: The key of the object. Can be None for unspecified objects.

        Returns:
            A MagicObject instance configured for this bucket and key.
        """
        if self.data_path:
            return MagicObject(Bucket=self.name, Key=key, DataPath=self.data_path)
        else:
            return MagicObject(Bucket=self.name, Key=key)


class MagicS3Client(BaseModel):
    """Emulate an S3 client to allow local filesystem storage via the S3 API.

    Provides client-level S3 operations that delegate to MagicBucket instances
    for bucket and object management. Maintains API compatibility with boto3
    S3 clients while using local filesystem storage.

    Supports both bucket operations and direct object operations, acting as
    the top-level interface for S3-like operations on local storage.

    Attributes:
        region: The AWS region (maintained for API compatibility).
        role_arn: The ARN of the role to assume (maintained for API compatibility).
        data_path: The root directory for local storage.
    """

    region: str = Field(
        default_factory=get_region,
        alias="Region",
        description="The AWS region for the client.",
    )
    role_arn: str | None = Field(
        default=None,
        alias="RoleArn",
        description="The ARN of the role to assume for the client.",
    )
    data_path: str | None = Field(
        alias="DataPath",
        default=None,
        description="The local storage path if not using S3.",
    )

    def head_object(self, **kwargs) -> dict:
        """Emulate the S3 client.head_object() method.

        Provides client-level access to object metadata operations by
        delegating to the appropriate bucket instance.

        Args:
            **kwargs: Keyword arguments.
                Bucket (str): The name of the bucket.
                Key (str): The key of the object to get metadata for.

        Returns:
            A dictionary of the object's metadata.
        """
        bucket_name = kwargs.pop("Bucket", None)
        bucket = self.Bucket(bucket_name)
        return bucket.head_object(**kwargs)

    def download_fileobj(self, **kwargs) -> dict:
        """Emulate the S3 client.download_fileobj() method.

        Provides client-level access to object download operations by
        delegating to the appropriate bucket instance.

        Args:
            **kwargs: Keyword arguments.
                Bucket (str): The name of the bucket.
                Key (str): The key of the object to download.
                Fileobj (IO): File-like object to write the downloaded content to.

        Returns:
            A dictionary of the object's metadata after download.
        """
        bucket_name = kwargs.pop("Bucket", None)
        bucket = self.Bucket(bucket_name)
        return bucket.download_fileobj(**kwargs)

    def put_object(self, **kwargs) -> MagicObject:
        """Emulate the S3 client.put_object() method.

        Provides client-level access to object storage operations by
        delegating to the appropriate bucket instance.

        Args:
            **kwargs: Keyword arguments for the put operation.
                Bucket (str): The name of the bucket.
                Key (str): The key (path) of the object within the bucket.
                Body (IO | str | bytes): The content to store.
                Filename (str): Alternative to Body - path to a local file to upload.

        Returns:
            The MagicObject instance after the put operation.

        Raises:
            ValueError: If required parameters are missing or Body type is unsupported.
        """
        bucket_name = kwargs.pop("Bucket", None)
        bucket = self.Bucket(bucket_name)
        return bucket.put_object(**kwargs)

    def delete_object(self, **kwargs) -> dict:
        """Emulate the S3 client.delete_object() method.

        Provides client-level access to object deletion operations by
        delegating to the appropriate bucket instance.

        Args:
            **kwargs: Keyword arguments.
                Bucket (str): The name of the bucket.
                Key (str): The key of the object to delete.

        Returns:
            A dictionary indicating the result of the delete operation.
        """
        bucket_name = kwargs.pop("Bucket", None)
        bucket = self.Bucket(bucket_name)
        return bucket.delete_object(**kwargs)

    def Bucket(self, bucket_name: str) -> MagicBucket:
        """Create a MagicBucket instance for the specified bucket name.

        Emulates the S3 client.Bucket() method to return a MagicBucket
        configured with this client's settings.

        Args:
            bucket_name: The name of the bucket.

        Returns:
            A MagicBucket instance configured for the specified bucket.
        """
        return MagicBucket(Bucket=bucket_name, DataPath=self.data_path)

    @staticmethod
    def get_bucket(
        Region: str, BucketName: str, RoleArn: str = None, DataPath: str | None = None
    ) -> Any:
        """Get a Bucket object, either real S3 or MagicBucket based on configuration.

        Provides transparent switching between real S3 and local storage based
        on the is_use_s3() configuration setting. Enables seamless development
        and testing without code changes.

        Args:
            Region: The AWS region of the bucket.
            BucketName: The name of the bucket.
            RoleArn: The ARN of the role to assume for the client. Optional.
            DataPath: The local storage path if not using S3. Optional.

        Returns:
            Either a boto3 S3 Bucket or a MagicBucket instance depending
            on configuration.

        Notes:
            - Uses is_use_s3() to determine which implementation to return
            - Real S3 buckets use aws.s3_resource() for creation
            - MagicBuckets use local filesystem storage
            - API compatibility is maintained regardless of implementation
        """

        if is_use_s3():
            s3 = aws.s3_resource(region=Region, role_arn=RoleArn)
            bucket = s3.Bucket(BucketName)
        else:
            local = MagicS3Client(Region=Region, RoleArn=RoleArn, DataPath=DataPath)
            bucket = local.Bucket(BucketName)

        return bucket

    @staticmethod
    def get_client(
        Region: str, RoleArn: str = None, DataPath: str | None = None
    ) -> Any:
        """Get an S3 client, either real boto3 or MagicS3Client based on configuration.

        Provides transparent switching between real S3 and local storage based
        on the is_use_s3() configuration setting for client-level operations.

        Args:
            Region: The AWS region for the client.
            RoleArn: The ARN of the role to assume for the client. Optional.
            DataPath: The local storage path if not using S3. Optional.

        Returns:
            Either a boto3 S3 client or a MagicS3Client instance depending
            on configuration.

        Notes:
            - Uses is_use_s3() to determine which implementation to return
            - Real S3 clients use aws.s3_client() for creation
            - MagicS3Client uses local filesystem storage
            - Full API compatibility maintained for all operations
        """
        if is_use_s3():
            client = aws.s3_client(region=Region, role_arn=RoleArn)
        else:
            client = MagicS3Client(Region=Region, RoleArn=RoleArn, DataPath=DataPath)

        return client


class SeekableStreamWrapper:
    """Wrapper that makes a streaming body seekable by buffering chunks.

    Provides seek functionality for non-seekable streams by buffering content
    as it's read. Useful for making streaming responses seekable for processing
    that requires random access to stream data.

    The wrapper reads chunks from the original stream on-demand and maintains
    an internal buffer to support seek operations. This enables compatibility
    with code that expects seekable streams.

    Attributes:
        stream: The original stream to wrap.
        chunk_size: Size of chunks to read when buffering.
        buffer: Internal buffer for storing read data.
        position: Current position in the buffered data.
        eof_reached: Flag indicating if end of stream was reached.
    """

    def __init__(self, stream, chunk_size: int = 8192):
        """Initialize the seekable stream wrapper.

        Args:
            stream: The original stream to wrap. Should have a read() method.
            chunk_size: Size of chunks to read when buffering. Larger chunks
                       use more memory but may be more efficient for large streams.
        """
        self.stream = stream
        self.chunk_size = chunk_size
        self.buffer = bytearray()
        self.position = 0
        self.eof_reached = False

    def read(self, size: int = -1) -> bytes:
        """Read up to size bytes from the wrapped stream.

        Buffers additional data from the underlying stream as needed to
        satisfy the read request. Maintains current position in the buffer.

        Args:
            size: Number of bytes to read. If -1, reads all remaining data.

        Returns:
            The bytes read from the stream.

        Notes:
            - Automatically buffers more data if needed
            - Updates internal position after reading
            - Returns empty bytes when end of stream is reached
        """
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
        """Seek to a specific position in the stream.

        Supports standard seek modes (absolute, relative, from end) and
        ensures the requested position is within valid bounds.

        Args:
            offset: The offset to seek to.
            whence: How to interpret the offset:
                   0 (SEEK_SET): Absolute position from start
                   1 (SEEK_CUR): Relative to current position
                   2 (SEEK_END): Relative to end of stream

        Returns:
            The new absolute position in the stream.

        Notes:
            - SEEK_END requires reading the entire stream to determine size
            - Position is clamped to valid range [0, buffer_length]
            - Automatically buffers data as needed for seeking
        """
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
        """Ensure the buffer contains at least target_size bytes.

        Reads additional chunks from the underlying stream until the buffer
        is large enough or end of stream is reached.

        Args:
            target_size: Minimum number of bytes needed in the buffer.
        """
        while len(self.buffer) < target_size and not self.eof_reached:
            chunk = self.stream.read(self.chunk_size)
            if not chunk:
                self.eof_reached = True
                break
            self.buffer.extend(chunk)

    def _read_all(self):
        """Read all remaining data from the underlying stream into the buffer.

        Continues reading chunks until end of stream is reached, ensuring
        the entire stream content is buffered for seek operations.
        """
        while not self.eof_reached:
            chunk = self.stream.read(self.chunk_size)
            if not chunk:
                self.eof_reached = True
                break
            self.buffer.extend(chunk)
