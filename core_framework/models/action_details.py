"""Defines the class ActionDetails that provide information about where ActionSpec files are stored in S3 (or local filesystem)."""

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

    client: str = Field(
        alias="Client",  # Alias for PascalCase compatibility
        description="The client to use for the action",
        default=V_EMPTY,
    )
    bucket_name: str = Field(
        alias="BucketName",  # Alias for PascalCase compatibility
        description="The name of the S3 bucket where the action file is stored",
        default=V_EMPTY,
    )
    bucket_region: str = Field(
        alias="BucketRegion",  # Alias for PascalCase compatibility
        description="The region of the S3 bucket where the action file is stored",
        default=V_EMPTY,
    )
    key: str = Field(
        alias="Key",  # Alias for PascalCase compatibility
        description="The key prefix where the ation file is stored in s3.  Usually in the artefacts folder",
        default=V_EMPTY,
    )
    version_id: str | None = Field(
        alias="VersionId",  # Alias for PascalCase compatibility
        description="The version of the action file",
        default=None,
    )
    content_type: str = Field(
        alias="ContentType",  # Alias for PascalCase compatibility
        description="The content type of the action file such as 'application/json' or 'application/x-yaml'",
        default="application/x-yaml",
    )

    @property
    def mode(self) -> str:
        """The mode of the application.  Either local or service"""
        return V_LOCAL if util.is_local_mode() else V_SERVICE

    @property
    def data_path(self) -> str:
        """The storage volume for the application. Used for local mode only else Blank  Defaults to the current directory."""
        return util.get_storage_volume()

    @property
    def temp_dir(self) -> str:
        """The temporary directory for the application.  Defaults to a temporary directory."""
        return util.get_temp_dir()

    @model_validator(mode="before")
    @classmethod
    def validate_artefacts_before(cls, values: Any) -> Any:
        if isinstance(values, dict):

            client = values.get("Client", values.get("client"))

            if not client:
                client = util.get_client()
                values["client"] = client

            region = values.get("BucketRegion", values.get("bucket_region", None))
            if region is None:
                region = util.get_artefact_bucket_region()
                values["bucket_region"] = region

            if not (values.get("BucketName") or values.get("bucket_name")):
                values["bucket_name"] = util.get_artefact_bucket_name(client, region)

        return values

    def set_key(self, dd: DeploymentDetailsClass, filename: str):
        self.key = dd.get_object_key(OBJ_ARTEFACTS, filename)

    @staticmethod
    def from_arguments(**kwargs) -> "ActionDetails":

        key = kwargs.get("key", kwargs.get("Key", V_EMPTY))
        if not key:
            task = kwargs.get("task", kwargs.get("Task", None))
            action_file = kwargs.get("action_file", kwargs.get("ActionFile", None))
            if task and not action_file:
                action_file = f"{task.lower()}.actions"
            dd = kwargs.get(
                "deployment_details", kwargs.get("DeploymentDetails", kwargs)
            )
            if not isinstance(dd, DeploymentDetailsClass):
                dd = DeploymentDetailsClass.from_arguments(**kwargs)
            if dd:
                key = dd.get_object_key(OBJ_ARTEFACTS, action_file)

        client = kwargs.get("client", kwargs.get("Client", util.get_client()))
        bucket_name = kwargs.get(
            "bucket_name",
            kwargs.get("BucketName", util.get_artefact_bucket_name(client)),
        )
        bucket_region = kwargs.get(
            "bucket_region",
            kwargs.get("BucketRegion", util.get_artefact_bucket_region()),
        )
        version_id = kwargs.get("version_id", kwargs.get("VersionId", None))
        content_type = kwargs.get(
            "content_type", kwargs.get("ContentType", "application/x-yaml")
        )

        return ActionDetails(
            client=client,
            bucket_name=bucket_name,
            bucket_region=bucket_region,
            key=key,
            varsion_id=version_id,
            content_type=content_type,
        )

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
