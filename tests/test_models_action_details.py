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
        ContentType="application/x-yaml",
    )
    dumped = action_details2.model_dump(by_alias=True)
    assert dumped["Client"] == "client2"
    assert dumped["BucketName"] == "bucket2"
    assert dumped["BucketRegion"] == "region2"
    assert dumped["Key"] == "key2"
    assert dumped["VersionId"] == "ver2"
    assert dumped["ContentType"] == "application/x-yaml"


def test_action_details_repr_and_eq():

    os.environ[ENV_LOCAL_MODE] = "false"  # ensure we are not in local mode
    os.environ[ENV_BUCKET_REGION] = "us-east-1"

    with pytest.raises(ValueError, match=r".*ContentType must be one of .* got: t1.*"):
        ActionDetails(
            client="c1",
            bucket_name="b1",
            bucket_region="r1",
            key="k1",
            version_id="v1",
            content_type="t1",  # invalid content type
        )

    ad1 = ActionDetails(
        client="c1",
        bucket_name="b1",
        bucket_region="r1",
        key="k1",
        version_id="v1",
        content_type="application/x-yaml",
    )

    ad2 = ActionDetails(
        client="c1",
        bucket_name="b1",
        bucket_region="r1",
        key="k1",
        version_id="v1",
        content_type="application/x-yaml",
    )
    assert ad1 == ad2
    assert str(ad1) == str(ad2)

    with pytest.raises(ValueError, match=""):
        ad1.mode = "buckets"

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
        content_type="application/x-yaml",  # Use valid content type
    )

    assert ad3.client == "client-12"
    assert ad3.bucket_name == "bucket_name"  # Use == instead of is
    assert ad3.bucket_region == "us-east-3"  # Use == instead of is

    # derive from parameters including environment variables
    ad4: ActionDetails = ActionDetails.from_arguments(
        **{
            "portfolio": "portfolio-1",
            "version_id": "v1",
            "content_type": "application/x-yaml",  # Use valid content type
            "deployment_details": V_EMPTY,  # force a type validation check for unit test
        }
    )

    assert ad4.client == "client-12"
    assert ad4.bucket_name == "bucket_name"
