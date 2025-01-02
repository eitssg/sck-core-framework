"""This module contains the PackageDetails class used to track where pacakge.zip is located on S3 for a deployment"""

from typing import Any

import os

from pydantic import BaseModel, Field, ConfigDict, model_validator

import core_framework as util

from .deployment_details import DeploymentDetails as DeploymentDetailsClass
from .deployspec import DeploySpec as DeploySpecClass

from core_framework.constants import (
    V_FULL,
    V_LOCAL,
    V_SERVICE,
    V_EMPTY,
    V_PACKAGE_ZIP,
    OBJ_PACKAGES,
)


class PackageDetails(BaseModel):
    """
    PackageDetails is a model that contains all of the information needed to locate and process a package.  A package is
    the artefact called "pacakge.zip" that is uploaded and contains all of the templates and resources necessary to
    perform a deployment.

    Typcially pacakges are in the packages folder **s3://<bucket>/packages/\\*\\***.

    Attributes:
        BucketRegion (str): The region of the bucket woere packages are stored.
        BucketName (str): The name of the bucket where packages are stored.
        Key (str): Key where the package is stored. Usually stored in packages/\\*\\*.
        Mode (str): The mode of the package.  Either "local" or "service".  defaults to "service"
        DataPath (str): The path to the application.  Used for local mode only.  Defaults to the current directory.
        CompileMode (str): The compile mode of the package.  Either "full" or "incremental".  Defaults to "full"
        DeploySpec (DeploySpecClass): DeploySpec is optional because it's added later by the lambda handlers
        TempDir (str): The temporary directory to use for processing the package.  Defaults to the system temp directory.
        VersionId (str): The version id of the package file (on S3).

    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    Client: str = Field(description="The client to use for the action", default="")
    BucketRegion: str = Field(
        description="The region of the bucket woere packages are stored.",
        default=V_EMPTY,
    )
    BucketName: str = Field(
        description="The name of the bucket where packages are stored.",
        default=V_EMPTY,
    )
    Key: str = Field(
        description="Key where the package is stored. Usually stored in packages/**",
        default=V_EMPTY,
    )
    CompileMode: str = Field(
        description="The compile mode of the package.  Either 'full' or 'incremental'.  Defaults to 'full'",
        default=V_FULL,
    )
    DeploySpec: DeploySpecClass | None = Field(
        description="DeploySpec is optional because it's added later by the lambda handlers",
        default=None,
    )
    VersionId: str | None = Field(
        description="The version id of the package file (on S3).", default=None
    )
    ContentType: str | None = Field(
        description="The content type of the package file such as 'appication/zip'",
        default="application/zip",
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
        """The temporary directory to use for processing the package.  Defaults to the system temp directory."""
        return util.get_temp_dir()

    @model_validator(mode="before")
    def validate_artefacts_before(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if not values.get("Client"):
                values["Client"] = util.get_client()
            if not values.get("BucketName"):
                values["BucketName"] = util.get_bucket_name(values["Client"])
            if not values.get("BucketRegion"):
                values["BucketRegion"] = util.get_bucket_region()
        return values

    def get_name(self) -> str:
        if not self.Key:
            return V_PACKAGE_ZIP
        sep = os.path.sep if self.Mode == V_LOCAL else "/"
        return self.Key.rsplit(sep, 1)[-1]

    def set_key(self, dd: DeploymentDetailsClass, filename: str):
        self.Key = dd.get_object_key(OBJ_PACKAGES, filename)

    @staticmethod
    def from_arguments(**kwargs) -> "PackageDetails":

        key = kwargs.get("key", kwargs.get("package_key", V_EMPTY))
        package_file = kwargs.get("package_file", V_PACKAGE_ZIP)
        if not key:
            dd = kwargs.get("deployment_details", kwargs)
            if not isinstance(dd, DeploymentDetailsClass):
                dd = DeploymentDetailsClass.from_arguments(**kwargs)
            if dd:
                key = dd.get_object_key(OBJ_PACKAGES, package_file)

        client = kwargs.get("client", util.get_client())
        bucket_name = kwargs.get("bucket_name", util.get_bucket_name(client))
        bucket_region = kwargs.get("bucket_region", util.get_bucket_region())
        content_type = kwargs.get("content_type", "application/zip")
        version_id = kwargs.get("version_id", None)

        deployspec = kwargs.get("deployspec", None)
        if isinstance(
            deployspec, dict
        ):  # You accidentally used a ActionSpec instead of a DeploySpec object
            deployspec = [deployspec]
        if isinstance(deployspec, list):  # A deployspec object is a list[ActionSpec]
            deployspec = DeploySpecClass(actions=deployspec)
        if not isinstance(deployspec, DeploySpecClass):
            deployspec = None

        compile_mode = kwargs.get("compile_mode", V_FULL)

        return PackageDetails(
            Client=client,
            BucketName=bucket_name,
            BucketRegion=bucket_region,
            Key=key,
            CompileMode=compile_mode,
            DeploySpec=deployspec,
            ContentType=content_type,
            VersionId=version_id,
        )

    # Override
    def model_dump(self, **kwargs) -> dict:
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
