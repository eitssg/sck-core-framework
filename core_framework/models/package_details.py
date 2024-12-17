import os

from pydantic import BaseModel, Field, model_validator, ConfigDict

import tempfile

import core_framework as util

from .deployment_details import DeploymentDetails as DeploymentDetailsClass
from .deployspec import DeploySpec as DeploySpecClass

from core_framework.constants import (
    V_FULL,
    V_LOCAL,
    V_SERVICE,
    V_EMPTY,
    OBJ_PACKAGES,
)


class PackageDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    BucketRegion: str | None = None
    """ The region of the bucket woere packages are stored. """

    BucketName: str | None = None
    """ The name of the bucket where packages are stored. """

    Key: str | None = None
    """ Key where the package is stored. Usually stored in packages/** """

    Mode: str = V_SERVICE
    """ The mode of the package.  Either "local" or "service".  defaults to "service"' """

    AppPath: str = V_EMPTY
    """ The path to the application.  Used for local mode only.  Defaults to the current directory. """

    CompileMode: str = V_FULL
    """ The compile mode of the package.  Either "full" or "incremental".  Defaults to "full" """

    DeploySpec: DeploySpecClass | None = None
    """ DeploySpec is optional because it's added later by the lambda handlers """

    TempDir: str | None = None
    """ The temporary directory to use for processing the package.  Defaults to the system temp directory. """

    VersionId: str | None = None
    """ The version id of the package file (on S3). """

    @model_validator(mode="before")
    def validate_packages_before(cls, values: dict) -> dict:
        if not values.get("BucketRegion"):
            values["BucketRegion"] = util.get_bucket_region()
        if not values.get("BucketName"):
            values["BucketName"] = util.get_bucket_name(util.get_client())
        if not values.get("TempDir"):
            values["TempDir"] = cls.get_tempdir()
        if not values.get("Mode"):
            values["Mode"] = V_LOCAL if util.is_local_mode() else V_SERVICE
        return values

    @classmethod
    def get_tempdir(cls) -> str:
        return tempfile.gettempdir()

    @staticmethod
    def from_arguments(**kwargs):

        mode = kwargs.get("mode", V_LOCAL if util.is_local_mode() else V_SERVICE)

        key = kwargs.get("key", None)
        if not key:
            dd = kwargs.get("deployment_details", None)
            if not isinstance(dd, DeploymentDetailsClass):
                dd = DeploymentDetailsClass.from_arguments(**kwargs)
            if dd:
                key = util.get_object_key(
                    dd, OBJ_PACKAGES, None, dd.Scope, mode != V_LOCAL
                )

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
        if not app_path:
            app_path = (
                os.path.join(os.getcwd(), V_LOCAL) if mode == V_LOCAL else V_EMPTY
            )

        compile_mode = kwargs.get("compile_mode", V_FULL)

        temp_dir = kwargs.get("tempdir", PackageDetails.get_tempdir())

        return PackageDetails(
            BucketName=bucket_name,
            BucketRegion=bucket_region,
            Key=key,
            Mode=mode,
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
