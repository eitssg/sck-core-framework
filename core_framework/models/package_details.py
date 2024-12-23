""" This module contains the PackageDetails class used to track where pacakge.zip is located on S3 for a deployment """
from typing import Any

import os

from pydantic import BaseModel, Field, ConfigDict, model_validator

import tempfile

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
        AppPath (str): The path to the application.  Used for local mode only.  Defaults to the current directory.
        CompileMode (str): The compile mode of the package.  Either "full" or "incremental".  Defaults to "full"
        DeploySpec (DeploySpecClass): DeploySpec is optional because it's added later by the lambda handlers
        TempDir (str): The temporary directory to use for processing the package.  Defaults to the system temp directory.
        VersionId (str): The version id of the package file (on S3).

    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    BucketRegion: str = Field(
        description="The region of the bucket woere packages are stored.",
        default=V_EMPTY,
    )
    BucketName: str = Field(
        description="The name of the bucket where packages are stored.",
        default=V_EMPTY,
    )
    Key: str | None = Field(
        description="Key where the package is stored. Usually stored in packages/**",
        default=None,
    )
    CompileMode: str = Field(
        description="The compile mode of the package.  Either 'full' or 'incremental'.  Defaults to 'full'",
        default=V_FULL,
    )
    DeploySpec: DeploySpecClass | None = Field(
        description="DeploySpec is optional because it's added later by the lambda handlers",
        default=None,
    )
    TempDir: str = Field(
        description="The temporary directory to use for processing the package.  Defaults to the system temp directory.",
        default=V_EMPTY,
    )
    VersionId: str | None = Field(
        description="The version id of the package file (on S3).", default=None
    )

    @property
    def Mode(self) -> str:
        """ The mode of the application.  Either local or service """
        return V_LOCAL if util.is_local_mode() else V_SERVICE

    @property
    def AppPath(self) -> str:
        """ The storage volume for the application. Used for local mode only else Blank  Defaults to the current directory. """
        return util.get_storage_volume()

    @model_validator(mode="before")
    def validate_artefacts_before(cls, values: Any) -> Any:
        if isinstance(values, dict):
            client = values.get("Client", util.get_client())
            if not values.get("BucketName"):
                values["BucketName"] = util.get_bucket_name(client)
            if not values.get("BucketRegion"):
                values["BucketRegion"] = util.get_bucket_region()
        return values

    @model_validator(mode="after")
    def validate(self):
        if not self.Mode:
            self.Mode = V_LOCAL if util.is_local_mode() else V_SERVICE
        if not self.TempDir:
            self.TempDir = self.get_tempdir()
        if self.Mode == V_LOCAL and not self.AppPath:
            self.AppPath = os.path.join(os.getcwd(), V_LOCAL)

        return self

    def set_key(self, dd: DeploymentDetailsClass, filename: str):
        self.Key = dd.get_object_key(OBJ_PACKAGES, filename, s3=self.Mode != V_LOCAL)

    @classmethod
    def get_tempdir(cls) -> str:
        return tempfile.gettempdir()

    @staticmethod
    def from_arguments(**kwargs):

        key = kwargs.get("key", None)
        package_file = kwargs.get("package_file", V_PACKAGE_ZIP)
        if not key:
            dd = kwargs.get("deployment_details", kwargs)
            if not isinstance(dd, DeploymentDetailsClass):
                dd = DeploymentDetailsClass.from_arguments(**kwargs)
            if dd:
                key = dd.get_object_key(OBJ_PACKAGES, package_file, s3=not util.is_local_mode())

        client = kwargs.get("client", util.get_client())
        bucket_name = kwargs.get("bucket_name", util.get_bucket_name(client))
        bucket_region = kwargs.get("bucket_region", util.get_bucket_region())

        deployspec = kwargs.get("deployspec", None)
        if isinstance(
            deployspec, dict
        ):  # You accidentally used a ActionSpec instead of a DeploySpec object
            deployspec = [deployspec]
        if isinstance(deployspec, list):  # A deployspec object is a list[ActionSpec]
            deployspec = DeploySpecClass(actions=deployspec)
        if not isinstance(deployspec, DeploySpecClass):
            deployspec = None

        app_path = kwargs.get("app_path", None)
        if not app_path and util.is_local_mode():
            app_path = util.get_storage_volume()

        compile_mode = kwargs.get("compile_mode", V_FULL)

        temp_dir = kwargs.get("tempdir", PackageDetails.get_tempdir())

        return PackageDetails(
            BucketName=bucket_name,
            BucketRegion=bucket_region,
            Key=key,
            AppPath=app_path,
            CompileMode=compile_mode,
            TempDir=temp_dir,
            DeploySpec=deployspec,
        )

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
