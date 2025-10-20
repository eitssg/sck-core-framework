import pytest
import os

import core_framework as util

from core_helper.magic import MagicS3Client, MagicBucket, MagicObject


test_folder = os.path.dirname(__file__)


def test_magic_client():

    os.environ["VOLUME"] = test_folder
    os.environ["LOCAL_MODE"] = "true"  # force get_client() to return MagicS3Client, not a boto3 S3 client

    # in our tests folder, we have a "templates" bucket (subfolder) with two files
    client: MagicS3Client = MagicS3Client.get_client(Region="local")
    assert isinstance(client, MagicS3Client)

    bucket: MagicBucket = client.Bucket("templates")
    assert bucket.name == "templates"
    assert bucket.data_path == test_folder

    # Test Object method
    obj: MagicObject = bucket.Object("test_filters.yaml.j2")
    assert obj.key == "test_filters.yaml.j2"
    assert obj.bucket_name == "templates"
    assert obj.data_path == test_folder

    # Test list_objects_v2 with default parameters
    response = client.list_objects_v2(Bucket="templates")
    assert isinstance(response, dict)
    assert response["Name"] == "templates"
    assert response["MaxKeys"] == 1000
    assert response["KeyCount"] == 2  # we have two jinja2 files in templates/
    keys = [item["Key"] for item in response.get("Contents", [])]
    assert "test_filters.yaml.j2" in keys
    assert "test_render.yaml.j2" in keys
