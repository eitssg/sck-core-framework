from typing import Any
import tempfile
from pydantic import BaseModel, ConfigDict, Field, model_validator

import core_framework as util
from core_framework.constants import OBJ_ARTEFACTS, V_LOCAL, V_SERVICE
from .deployment_details import DeploymentDetails as DeploymentDetailsClass


class StateDetails(BaseModel):
    """
    ActionDetails: The details of the action location in S3.  Typically the "artefacts" folder
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    BucketName: str
    BucketRegion: str
    Key: str = Field(
        "artefacts",
        description="The key prefix where the ation file is stored in s3.  Usually in the artefacts folder",
    )
    VersionId: str | None = Field(None, description="The version of the state file")
    ContentType: str | None = Field(
        None,
        description="The content type of the state file. Usually 'application/json' or 'application/x-yaml'",
    )

    @model_validator(mode="before")
    def validate_artefacts_before(cls, values: Any) -> Any:
        if isinstance(values, dict):
            client = values.get("Client", util.get_client())
            if not values.get("BucketName"):
                values["BucketName"] = util.get_artefact_bucket_name(client)
            if not values.get("BucketRegion"):
                values["BucketRegion"] = util.get_artefact_bucket_region()
        return values

    @classmethod
    def get_tempdir(cls) -> str:
        tmpdir = tempfile.mkdtemp(prefix="core-")
        return tmpdir

    @staticmethod
    def from_arguments(**kwargs):

        client = kwargs.get("client", util.get_client())

        mode = kwargs.get("mode", V_LOCAL if util.is_local_mode() else V_SERVICE)

        key = kwargs.get("key", None)
        if not key:
            dd = kwargs.get("deployment_details", kwargs)
            if not isinstance(dd, DeploymentDetailsClass):
                dd = DeploymentDetailsClass.from_arguments(**kwargs)
            if dd:
                key = util.get_object_key(
                    dd, OBJ_ARTEFACTS, None, dd.Scope, mode != V_LOCAL
                )

        bucket_name = kwargs.get("bucket_name", util.get_artefact_bucket_name(client))
        bucket_region = kwargs.get("bucket_region", util.get_artefact_bucket_region())

        version_id = kwargs.get("version_id", None)

        return StateDetails(
            BucketName=bucket_name,
            BucketRegion=bucket_region,
            Key=key,
            VersionId=version_id,
        )

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
