import os
import io
import shutil


class MagicBucket:

    bucket_name = None
    bucket_region = None

    def __init__(self, bucket_name, bucket_region):
        self.bucket_name = bucket_name
        self.bucket_region = bucket_region

    def Object(self, key):
        return MagicObject(self.bucket_name, self.bucket_region, key)

    def download_fileobj(self, **kwargs):
        key = kwargs.get("Key")
        fileobj = kwargs.get("Fileobj")
        # extra_args = kwargs.get("ExtraArgs")

        if key and fileobj:
            with open(key, "rb") as file:
                fileobj.write(file.read())
            fileobj.seek(0)


class MagicObject:
    bucket_name = None
    bucket_region = None
    key = None
    version_id = None

    def __init__(self, bucket_name, bucket_region, key):
        self.bucket_name = bucket_name
        self.bucket_region = bucket_region
        self.key = key
        self.version_id = None

    def copy_from(self, **kwargs) -> dict:

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

    def __init__(self, **kwargs):
        self.bucket_name = kwargs.get("bucket_name")
        self.region = kwargs.get("region")

    def download_fileobj(self, **kwargs) -> dict:
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
