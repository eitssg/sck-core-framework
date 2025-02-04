"""Defines the class ActionDetails that provide information about where ActionDefinition files are stored in S3 (or local filesystem)."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

import core_framework as util
from core_framework.constants import OBJ_ARTEFACTS, V_LOCAL, V_SERVICE, V_EMPTY
from .deployment_details import DeploymentDetails as DeploymentDetailsClass


class ActionDetails(BaseModel):
    """
    ActionDetails: The details of the action location in S3.  Typically the "artefacts" folder

    Attributes:
        BucketName (str): The name of the S3 bucket where the action file is stored
        BucketRegion (str): The region of the S3 bucket where the action file is stored
        Key (str): The key prefix where the ation file is stored in s3.  Usually in the artefacts folder
        VersionId (str): The version of the action file
        ContentType (str): The content type of the action file such as 'application/json' or 'application/x-yaml'

    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    Client: str = Field(description="The client to use for the action", default=V_EMPTY)
    BucketName: str = Field(
        description="The name of the S3 bucket where the action file is stored",
        default=V_EMPTY,
    )
    BucketRegion: str = Field(
        description="The region of the S3 bucket where the action file is stored",
        default=V_EMPTY,
    )
    Key: str = Field(
        description="The key prefix where the ation file is stored in s3.  Usually in the artefacts folder",
        default=V_EMPTY,
    )
    VersionId: str | None = Field(
        description="The version of the action file", default=None
    )
    ContentType: str = Field(
        description="The content type of the action file such as 'application/json' or 'application/x-yaml'",
        default="application/x-yaml",
    )

    @property
    def Mode(self) -> str:
        """The mode of the application.  Either local or service"""
        return V_LOCAL if util.is_local_mode() else V_SERVICE

    @property
    def DataPath(self) -> str:
        """The storage volume for the application. Used for local mode only else Blank  Defaults to the current directory."""
        return util.get_storage_volume()

    @property
    def TempDir(self) -> str:
        """The temporary directory for the application.  Defaults to a temporary directory."""
        return util.get_temp_dir()

    @model_validator(mode="before")
    @classmethod
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
        self.Key = dd.get_object_key(OBJ_ARTEFACTS, filename)

    @staticmethod
    def from_arguments(**kwargs) -> "ActionDetails":

        key = kwargs.get("key", V_EMPTY)
        if not key:
            task = kwargs.get("task", None)
            action_file = kwargs.get("action_file", None)
            if task and not action_file:
                action_file = f"{task.lower()}.actions"
            dd = kwargs.get("deployment_details", kwargs)
            if not isinstance(dd, DeploymentDetailsClass):
                dd = DeploymentDetailsClass.from_arguments(**kwargs)
            if dd:
                key = dd.get_object_key(OBJ_ARTEFACTS, action_file)

        client = kwargs.get("client", util.get_client())
        bucket_name = kwargs.get("bucket_name", util.get_artefact_bucket_name(client))
        bucket_region = kwargs.get("bucket_region", util.get_artefact_bucket_region())
        version_id = kwargs.get("version_id", None)
        content_type = kwargs.get("content_type", "application/x-yaml")

        return ActionDetails(
            Client=client,
            BucketName=bucket_name,
            BucketRegion=bucket_region,
            Key=key,
            VersionId=version_id,
            ContentType=content_type,
        )

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
