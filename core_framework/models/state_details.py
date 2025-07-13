"""This module contains the StateDetails class which provides information about the current state of the deployment."""

from typing import Any, Self
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

    client: str = Field(
        alias="Client",  # Alias for PascalCase compatibility
        description="The client to use for the action.  Defaults to the current client.",
        default=V_EMPTY,
    )
    bucket_name: str = Field(
        alias="BucketName",  # Alias for PascalCase compatibility
        description="The name of the S3 bucket where the state file is stored.",
        default=V_EMPTY,
    )
    bucket_region: str = Field(
        alias="BucketRegion",  # Alias for PascalCase compatibility
        description="The region of the S3 bucket where the state file is stored.",
        default=V_EMPTY,
    )
    key: str = Field(
        alias="Key",  # Alias for PascalCase compatibility
        description="The key prefix where the ation file is stored in s3.  Usually in the artefacts folder",
        default=V_EMPTY,
    )
    version_id: str | None = Field(
        alias="VersionId",  # Alias for PascalCase compatibility
        description="The version of the state file",
        default=None,
    )
    content_type: str = Field(
        alias="ContentType",  # Alias for PascalCase compatibility
        description="The content type of the state file. Usually 'application/json' or 'application/x-yaml'",
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
        """The temporary directory to use for local mode.  Defaults to the system temp directory."""
        return util.get_temp_dir()

    @model_validator(mode="before")
    def validate_artefacts_before(cls, values: Any) -> Any:
        if isinstance(values, dict):

            client = values.get("Client", values.get("client", V_EMPTY))
            if not client:
                client = util.get_client()
                values["client"] = client

            region = values.get("BucketRegion", values.get("bucket_region", V_EMPTY))
            if not region:
                region = util.get_artefact_bucket_region()
                values["bucket_region"] = region

            if not (values.get("BucketName") or values.get("bucket_name")):
                values["bucket_name"] = util.get_artefact_bucket_name(client, region)

        return values

    def set_key(self, dd: DeploymentDetailsClass, filename: str):
        self.key = dd.get_object_key(OBJ_ARTEFACTS, filename)

    @staticmethod
    def from_arguments(**kwargs) -> "StateDetails":

        key = kwargs.get("key", kwargs.get("Key", V_EMPTY))
        if not key:
            state_file = kwargs.get("state_file", kwargs.get("StateFile", None))
            task = kwargs.get("task", kwargs.get("Task", None))
            if task and state_file is None:
                state_file = f"{task}.state"
            dd = kwargs.get("deployment_details", kwargs.get("DeploymentDetails", None))
            if not isinstance(dd, DeploymentDetailsClass):
                dd = DeploymentDetailsClass.from_arguments(**kwargs)
            if dd:
                key = dd.get_object_key(OBJ_ARTEFACTS, state_file)

        client = kwargs.get("client", kwargs.get("Client", util.get_client()))
        bucket_name = kwargs.get(
            "bucket_name",
            kwargs.get("BucketName", util.get_artefact_bucket_name(client)),
        )
        bucket_region = kwargs.get(
            "bucket_region",
            kwargs.get("BucketRegion", util.get_artefact_bucket_region()),
        )
        content_type = kwargs.get(
            "content_type", kwargs.get("ContentType", "application/x-yaml")
        )
        version_id = kwargs.get("version_id", kwargs.get("VersionId", None))

        return StateDetails(
            client=client,
            bucket_name=bucket_name,
            bucket_region=bucket_region,
            key=key,
            version_id=version_id,
            content_type=content_type,
        )

    # Override
    def model_dump(self, **kwargs) -> dict:
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
