""" Magic module for emulating the boto3 S3 client and Buckets so we can elect to store files locally instead of in S3 """

from typing import Any, Self
import os
import shutil
import mimetypes
import hashlib
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, model_validator

from .common import get_storage_volume, get_bucket_name, get_region


class MagicObject(BaseModel):
    """
    MagicObject class to emulate an S3 Object.  Currently only emulates the "copy_from" method.

    The purpose is to copy objects from the local filesystem instead of S3 using s3 api.

    """

    model_config = ConfigDict(populate_by_name=True)

    bucket_name: str = Field(default_factory=get_bucket_name, alias="Bucket")
    bucket_region: str = Field(default_factory=get_region, alias="Region")
    key: str | None = Field(default=None, alias="Key")
    app_path: str = Field(default_factory=get_storage_volume, alias="AppPath")
    version_id: str | None = Field(default=None, alias="VersionId")
    content_type: str | None = Field(default=None, alias="ContentType")
    etag: str | None = Field(default=None, alias="ETag")
    error: str | None = Field(default=None, alias="Error")

    @model_validator(mode="before")
    @classmethod
    def validaate_before(cls, v) -> Any:
        if isinstance(v, dict):
            if not v.get("bucket_name"):
                v["bucket_name"] = get_bucket_name()
            if not v.get("bucket_region"):
                v["bucket_region"] = get_region()
            if not v.get("app_path"):
                v["app_path"] = get_storage_volume()
        return v

    def head_object(self, **kwargs) -> Self:
        """Emulate the S3 head_object() API method to get the metadata of an object"""
        try:
            self.key = kwargs.get("Key", self.key)
            if not self.key:
                raise ValueError("Key is required")

            fn = os.path.join(self.app_path, self.bucket_name, self.key)

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

    def generate_file_hash(self, file_path, hash_algorithm="sha256"):
        """
        Generate a hash of a file.

        Args:
            file_path (str): The path to the file.
            hash_algorithm (str): The hash algorithm to use (default: 'sha256').

        Returns:
            str: The hexadecimal hash of the file.
        """
        hash_func = hashlib.new(hash_algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    def copy_from(self, **kwargs) -> dict:  # noqa: C901
        """Copies the artefact on the local filessystem instead of S3

        Args:
            CopySource (dict): The source object to copy from
            Bucket (str): The source bucket name
            Key (str): The source key

        """
        try:
            source = kwargs.get("CopySource", None)
            source_bucket = source.get("Bucket", None)
            source_key = source.get("Key", None)

            if not source:
                raise ValueError("Copy source 'CopySource' is required")

            if not source_bucket:
                raise ValueError("Source bucket 'Bucket' is required")

            if not source_key:
                raise ValueError("Source key 'Key' is required")

            if not self.key:
                raise ValueError("Destination Bucket ke has not been specified")

            if source_bucket != self.bucket_name:
                raise ValueError(
                    "Source S3 bucket '{}' must be in same bucket as the target '{}'".format(
                        source, self.bucket_name
                    )
                )

            source_fn = os.path.join(self.app_path, source_bucket, source_key)
            target_fn = os.path.join(self.app_path, self.bucket_name, self.key)

            if source_key and self.key:
                os.makedirs(os.path.dirname(target_fn), exist_ok=True)
                shutil.copy(source_fn, target_fn)
            else:
                raise ValueError("Source and destination keys are required")

            self.head_object()

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        if self.version_id:
            dt = datetime.fromtimestamp(int(self.version_id)).isoformat()
        else:
            dt = None

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
        """
        Emulate the S3 download_fileobj() API method to download a fileobj from the local filesystem.

        Args:
            Key (str): The key of the object
            Fileobj (file): The file object to write the data to
        """
        try:
            self.key = kwargs.get("Key", self.key)
            if not self.key:
                raise ValueError("Key is required")

            key = os.path.join(self.app_path, self.bucket_name, self.key)

            fileobj = kwargs.get("Fileobj")
            if fileobj is None:
                raise ValueError("Fileobj is required")

            # extra_args = kwargs.get("ExtraArgs")
            if os.path.exists(key):
                with open(key, "rb") as file:
                    fileobj.write(file.read())
                fileobj.seek(0)

            self.head_object()

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        return self

    def put_object(self, **kwargs) -> Self:
        """Put an object on the local filesystem instead of S3"""

        try:
            self.key = kwargs.get("Key", self.key)
            if not self.key:
                raise ValueError("Key is required")

            body = kwargs.get("Body")

            if not body:
                raise ValueError("Body is required")

            fn = os.path.join(self.app_path, self.bucket_name, self.key)

            # get the directory of the file fn
            dirname = os.path.dirname(fn)
            os.makedirs(dirname, exist_ok=True)
            if isinstance(body, str):
                body = body.encode("utf-8")
            if isinstance(body, bytes):
                with open(fn, "wb") as file:
                    file.write(body)

            self.head_object()

        except Exception as e:
            self.error = "\n".join([self.error or "", str(e)])

        return self


class MagicBucket(BaseModel):
    """
    Provides a Magic Bucket with the S3 Bucket API for downloading fileobj and getting a MagicObject that behaves like an S3 Object.

    The purpose is to read objects from the local filesystem instead of S3 using s3 api.
    """

    bucket_name: str = Field(default_factory=get_bucket_name, alias="Bucket")
    bucket_region: str = Field(default_factory=get_region, alias="Region")
    app_path: str = Field(default_factory=get_storage_volume, alias="AppPath")

    @model_validator(mode="before")
    @classmethod
    def validate_before(cls, v) -> Any:
        # did you know, a bucket name and an app_path
        # are the same thing? I think we can combine them.
        if isinstance(v, dict):
            if not v.get("bucket_name"):
                v["bucket_name"] = get_bucket_name()
            if not v.get("bucket_region"):
                v["bucket_region"] = get_region()
            if not v.get("app_path"):
                v["app_path"] = get_storage_volume()
        return v

    def head_object(self, **kwargs) -> dict:
        """Emulate the S3 head_object() API method to get the metadata of an object"""

        key = kwargs.pop("Key", None)

        object = self.Object(key)

        return object.head_object(**kwargs).model_dump(exclude_none=True)

    def download_fileobj(self, **kwargs) -> dict:
        """Emulate the S3 download_fileobj() API method to download a fileobj from the local filesystem."""

        key = kwargs.pop("Key", None)

        object = self.Object(key)

        return object.download_fileobj(**kwargs).model_dump(exclude_none=True)

    def put_object(self, **kwargs) -> MagicObject:
        """Put an object on the local filesystem instead of S3"""

        key = kwargs.pop("Key", None)

        object = self.Object(key)

        return object.put_object(**kwargs)

    def Object(self, key: str | None) -> MagicObject:
        """
        Emulate the S3 Object() API method to return a MagicObject instead of an S3 Object

        Args:
            key (str): The key of the object

        Returns:
            MagicObject: A MagicObject that behaves like an S3 Object
        """
        return MagicObject(
            Bucket=self.bucket_name,
            Region=self.bucket_region,
            Key=key,
            AppPath=self.app_path,
        )


class MagicS3Client(BaseModel):
    """
    MagicS3Client class to emulate an S3 client.  Currently only emulates the "download_fileobj" and "put_object" methods.

    The purpose is to read and write objects to the local filesystem instead of S3 using s3 api.
    """

    bucket_name: str = Field(default_factory=get_bucket_name, alias="Bucket")
    region_name: str = Field(default_factory=get_region, alias="Region")
    app_path: str = Field(default_factory=get_storage_volume, alias="AppPath")

    @model_validator(mode="before")
    @classmethod
    def validate_before(cls, v) -> Any:
        if isinstance(v, dict):
            if not v.get("bucket_name"):
                v["bucket_name"] = get_bucket_name()
            if not v.get("region_name"):
                v["region_name"] = get_region()
            if not v.get("app_path"):
                v["app_path"] = get_storage_volume()
        return v

    def head_object(self, **kwargs) -> dict:
        """Emulate the S3 head_object() API method to get the metadata of an object"""

        bucket_name = kwargs.pop("Bucket", self.bucket_name)

        bucket = self.Bucket(bucket_name)

        return bucket.head_object(**kwargs)

    def download_fileobj(self, **kwargs) -> dict:
        """
        Emulate the S3 download_fileobj() API method to download a fileobj from the local filesystem.

        Args:
            Bucket (str): The name of the bucket
            Key (str): The key of the object
            Fileobj (file): The file object to write the data to
            ExtraArgs (dict): Extra arguments to pass to the download

        Raises:
            ValueError: If missing the Key or Fileobj buffer

        Returns:
            dict: A dictionary emulating what S3 would return for a download_fileobj() call
        """
        bucket_name = kwargs.pop("Bucket", self.bucket_name)

        bucket = self.Bucket(bucket_name)

        return bucket.download_fileobj(**kwargs)

    def put_object(self, **kwargs) -> MagicObject:
        """
        Emulate the S3 put_object() API method to store a file on the local filesystem.

        Args:
            Bucket (str): The name of the bucket
            Key (str): The key of the object
            Body (str): The body of the object
            ContentType (str): The content type of the object
            ServerSideEncryption (str): The server side encryption type

        Returns:
            dict: A dictionary that would emulate what S3 would return for a put_object() call
        """
        bucket_name = kwargs.pop("Bucket", self.bucket_name)

        bucket = self.Bucket(bucket_name)

        return bucket.put_object(**kwargs)

    def Bucket(self, bucket_name: str) -> MagicBucket:
        """
        Emulate the S3 Bucket() API method to return a MagicBucket instead of an S3 Bucket

        Args:
            bucket_name (str): The name of the bucket

        Returns:
            MagicBucket: A MagicBucket that behaves like an S3 Bucket
        """
        return MagicBucket(
            Bucket=bucket_name, Region=self.region_name, AppPath=self.app_path
        )
