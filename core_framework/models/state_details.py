""" This module contains the StateDetails class which provides information about the current state of the deployment."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

import core_framework as util
from core_framework.constants import OBJ_ARTEFACTS, V_LOCAL, V_SERVICE, V_EMPTY
from .deployment_details import DeploymentDetails as DeploymentDetailsClass


class StateDetails(BaseModel):
    """
    ActionDetails: The details of the action location in S3.  Typically the "artefacts" folder in a {task}.state file.

    The file is stored in S3 in the artefacts folder: **s3://client-bucket/artefacts/portfolio/app/branch/build/{task}.state**

    Attributes:
        BucketName (str): The name of the S3 bucket where the state file is stored.
        BucketRegion (str): The region of the S3 bucket where the state file is stored.
        Key (str): The key prefix where the state file is stored in s3.  Usually in the artefacts folder.
        VersionId (str | None): The version of the state file.
        ContentType (str | None): The content type of the state file. Usually 'application/json' or 'application/x-yaml
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    Client: str = Field(
        description="The client to use for the action.  Defaults to the current client.",
        default=V_EMPTY,
    )
    BucketName: str = Field(
        description="The name of the S3 bucket where the state file is stored.",
        default=V_EMPTY,
    )
    BucketRegion: str = Field(
        description="The region of the S3 bucket where the state file is stored.",
        default=V_EMPTY,
    )
    Key: str = Field(
        description="The key prefix where the ation file is stored in s3.  Usually in the artefacts folder",
        default=V_EMPTY,
    )
    VersionId: str | None = Field(
        description="The version of the state file", default=None
    )
    ContentType: str = Field(
        description="The content type of the state file. Usually 'application/json' or 'application/x-yaml'",
        default="application/x-yaml",
    )

    @property
    def Mode(self) -> str:
        """The mode of the application.  Either local or service"""
        return V_LOCAL if util.is_local_mode() else V_SERVICE

    @property
    def AppPath(self) -> str:
        """The storage volume for the application. Used for local mode only else Blank  Defaults to the current directory."""
        if util.is_local_mode():
            return util.get_storage_volume()
        return V_EMPTY

    @property
    def TempDir(self) -> str:
        """The temporary directory to use for local mode.  Defaults to the system temp directory."""
        if util.is_local_mode():
            return util.get_temp_dir()
        return V_EMPTY

    @model_validator(mode="before")
    def validate_artefacts_before(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if not values.get("Client"):
                values["Client"] = util.get_client()
            if not values.get("BucketName"):
                values["BucketName"] = util.get_artefact_bucket_name(values["Client"])
            if not values.get("BucketRegion"):
                values["BucketRegion"] = util.get_artefact_bucket_region()
        return values

    def set_key(self, dd: DeploymentDetailsClass, filename: str):
        self.Key = dd.get_object_key(
            OBJ_ARTEFACTS, filename, s3=not util.is_local_mode()
        )

    @staticmethod
    def from_arguments(**kwargs) -> "StateDetails":

        key = kwargs.get("key", None)
        if not key:
            state_file = kwargs.get("state_file", None)
            task = kwargs.get("task", None)
            if task and state_file is None:
                state_file = f"{task}.state"
            dd = kwargs.get("deployment_details", kwargs)
            if not isinstance(dd, DeploymentDetailsClass):
                dd = DeploymentDetailsClass.from_arguments(**kwargs)
            if dd:
                key = dd.get_object_key(
                    OBJ_ARTEFACTS, state_file, s3=not util.is_local_mode()
                )

        client = kwargs.get("client", util.get_client())
        bucket_name = kwargs.get("bucket_name", util.get_artefact_bucket_name(client))
        bucket_region = kwargs.get("bucket_region", util.get_artefact_bucket_region())
        content_type = kwargs.get("content_type", "application/x-yaml")
        version_id = kwargs.get("version_id", None)

        return StateDetails(
            Client=client,
            BucketName=bucket_name,
            BucketRegion=bucket_region,
            Key=key,
            VersionId=version_id,
            ContentType=content_type,
        )

    # Override
    def model_dump(self, **kwargs) -> dict:
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
