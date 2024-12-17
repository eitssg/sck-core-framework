""" Magic module for emulating the boto3 S3 client and Buckets so we can elect to store files locally instead of in S3 """

import os
import shutil


class MagicBucket:
    """
    Provides a Magic Bucket with the S3 Bucket API for downloading fileobj and getting a MagicObject that behaves like an S3 Object.
    """

    def __init__(self, bucket_name: str, bucket_region: str):
        """
        Initialize a MagicBucket object.

        Args:
            bucket_name (_type_): _description_
            bucket_region (_type_): _description_
        """
        self.bucket_name = bucket_name
        self.bucket_region = bucket_region

    def Object(self, key: str):
        """
        Emulate the S3 Object() API method to return a MagicObject instead of an S3 Object

        Args:
            key (str): The key of the object

        Returns:
            MagicObject: A MagicObject that behaves like an S3 Object
        """
        return MagicObject(self.bucket_name, self.bucket_region, key)

    def download_fileobj(self, **kwargs):
        """
        Emulate the S3 download_fileobj() API method to download a fileobj from the local filesystem.

        Args:
            Key (str): The key of the object
            Fileobj (file): The file object to write the data to
        """
        key = kwargs.get("Key")
        fileobj = kwargs.get("Fileobj")
        # extra_args = kwargs.get("ExtraArgs")

        if key and fileobj:
            with open(key, "rb") as file:
                fileobj.write(file.read())
            fileobj.seek(0)


class MagicObject:
    """
    MagicObject class to emulate an S3 Object.  Currently only emulates the "copy_from" method.

    """

    def __init__(self, bucket_name: str, bucket_region: str, key: str):
        """
        Initialize a MagicObject object.

        Args:
            bucket_name (str): The name of the bucket
            bucket_region (str): The region of the bucket
            key (str): The key of the object

        """
        self.bucket_name = bucket_name
        self.bucket_region = bucket_region
        self.key = key
        self.version_id = None

    def copy_from(self, **kwargs) -> dict:
        """Copies the artefact on the local filessystem instead of S3

        Args:
            CopySource (dict): The source object to copy from
            Bucket (str): The source bucket name
            Key (str): The source key

        """
        source = kwargs.get("CopySource", None)
        source_bucket = source.get("Bucket", None)
        source_key = source.get("Key", None)

        error = None

        try:
            if source_bucket != self.bucket_name:
                raise ValueError(
                    "Source S3 bucket must be in same bucket as the target '{}'".format(
                        self.bucket_name
                    )
                )

            if source_key and self.key:
                os.makedirs(os.path.dirname(self.key), exist_ok=True)
                shutil.copy(source_key, self.key)
            else:
                raise ValueError("Source and destination keys are required")

        except Exception as e:
            error = str(e)

        rv: dict = {
            "BucketName": self.bucket_name,
            "BucketRegion": self.bucket_region,
            "Key": self.key,
            "VersionId": self.version_id,
        }

        if error is not None:
            rv["Error"] = error

        return rv


class MagicS3Client:
    """
    MagicS3Client class to emulate an S3 client.  Currently only emulates the "download_fileobj" and "put_object" methods.

    """

    def __init__(self, **kwargs):
        """
        Initialze a MagicS3Client object

        Args:
            bucket_name (str): The name of the bucket
            region (str): The region of the bucket

        """
        self.bucket_name = kwargs.get("bucket_name")
        self.region = kwargs.get("region")

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
        self.bucket = kwargs.get("Bucket")
        Key = kwargs.get("Key")
        Fileobj = kwargs.get("Fileobj")
        ExtraArgs = kwargs.get("ExtraArgs")

        try:
            verion_id = None
            error = None
            if Key and Fileobj:
                with open(Key, "rb") as file:
                    Fileobj.write(file.read())
                Fileobj.seek(0)
                verion_id = "1"
            else:
                raise ValueError("Key and Fileobj are required")

        except Exception as e:
            error = str(e)

        rv = {
            "Bucket": self.bucket,
            "Key": Key,
            "ExtraArgs": ExtraArgs,
            "ContentType": "application/x-yaml",
            "VersionId": verion_id,
        }

        if error:
            rv["Error"] = error

        return rv

    def put_object(self, **kwargs) -> dict:
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

        self.bucket = kwargs.get("Bucket")
        Key = kwargs.get("Key")
        Body = kwargs.get("Body")
        ContentType = kwargs.get("ContentType")
        ServerSideEncryption = kwargs.get("ServerSideEncryption")

        version_id = None
        if Key and Body:
            try:
                os.makedirs(Key, exist_ok=True)
                if isinstance(Body, str):
                    Body = Body.encode("utf-8")
                if isinstance(Body, bytes):
                    with open(Key, "wb") as file:
                        file.write(Body)
                    version_id = "1"
            except Exception as e:
                error = str(e)

        rv = {
            "Bucket": self.bucket,
            "Key": Key,
            "ContentType": ContentType,
            "ServerSideEncryption": ServerSideEncryption,
            "VersionId": version_id,
        }

        if error:
            rv["Error"] = error

        return rv
