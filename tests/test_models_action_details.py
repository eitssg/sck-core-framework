import pytest
import os
from core_framework.models.action_details import ActionDetails
from core_framework.constants import (
    ENV_LOCAL_MODE,
    V_LOCAL,
    V_SERVICE,
    ENV_BUCKET_REGION,
    V_EMPTY,
    ENV_CLIENT,
    ENV_BUCKET_NAME,
)


def test_action_details_init_and_aliases():
    action_details = ActionDetails(
        client="my-client",
        bucket_name="my-bucket",
        bucket_region="us-east-1",
        key="artefacts/my-action.yaml",
        version_id="1234567890abcdef",
        content_type="application/x-yaml",
    )

    # Snake_case attribute access
    assert action_details.client == "my-client"
    assert action_details.bucket_name == "my-bucket"
    assert action_details.bucket_region == "us-east-1"
    assert action_details.key == "artefacts/my-action.yaml"
    assert action_details.version_id == "1234567890abcdef"
    assert action_details.content_type == "application/x-yaml"

    # PascalCase alias input and model_dump(by_alias=True)
    action_details2 = ActionDetails(
        Client="client2",
        BucketName="bucket2",
        BucketRegion="region2",
        Key="key2",
        VersionId="ver2",
        ContentType="type2",
    )
    dumped = action_details2.model_dump(by_alias=True)
    assert dumped["Client"] == "client2"
    assert dumped["BucketName"] == "bucket2"
    assert dumped["BucketRegion"] == "region2"
    assert dumped["Key"] == "key2"
    assert dumped["VersionId"] == "ver2"
    assert dumped["ContentType"] == "type2"


def test_action_details_repr_and_eq():
    ad1 = ActionDetails(
        client="c1",
        bucket_name="b1",
        bucket_region="r1",
        key="k1",
        version_id="v1",
        content_type="t1" "",
    )

    os.environ[ENV_BUCKET_REGION] = (
        "us-east-1"  # the data path test will use 'service' mode s3 bucket
    )

    ad2 = ActionDetails(
        client="c1",
        bucket_name="b1",
        bucket_region="r1",
        key="k1",
        version_id="v1",
        content_type="t1",
    )
    assert ad1 == ad2
    assert str(ad1) == str(ad2)

    os.environ[ENV_LOCAL_MODE] = "true"

    assert ad2.mode == V_LOCAL

    del os.environ[ENV_LOCAL_MODE]

    assert ad2.mode == V_SERVICE

    data_path = ad2.data_path

    os.environ["TEMP"] = "/tmp"

    assert (
        data_path == "https://s3-us-east-1.amazonaws.com"
    ), f"Expected 'https://s3-us-east-1.amazonaws.com', got {data_path}"

    temp_dir = ad2.temp_dir

    assert temp_dir == "/tmp", f"Expected '/tmp', got {temp_dir} "

    os.environ[ENV_CLIENT] = "client-12"
    os.environ[ENV_BUCKET_NAME] = "bucket_name"
    os.environ[ENV_BUCKET_REGION] = "us-east-3"

    # get client, bucket_name, and bucket_region from environment variables

    ad3 = ActionDetails(
        key="k1",
        version_id="v1",
        content_type="t1",
    )

    assert ad3.client == "client-12"
    assert ad3.bucket_name is "bucket_name"
    assert ad3.bucket_region is "us-east-3"

    # derrive from paramters including environtment variables

    ad4: ActionDetails = ActionDetails.from_arguments(
        **{
            "portfolio": "portfolio-1",
            "version_id": "v1",
            "content_type": "t1",
            "deployment_details": V_EMPTY,  # force a type validation check for unit test
        }
    )

    assert ad4.client == "client-12"
    assert ad4.bucket_name == "bucket_name"
