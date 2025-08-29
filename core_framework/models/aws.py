from datetime import datetime
from pydantic import BaseModel, Field


class AWSCredentials(BaseModel):
    access_key_id: str = Field(..., alias="AccessKeyId")
    secret_access_key: str = Field(..., alias="SecretAccessKey")
    session_token: str = Field(..., alias="SessionToken")
    expiration: datetime = Field(..., alias="Expiration")


class AWSAssumedRoleUser(BaseModel):
    assumed_role_id: str = Field(..., alias="AssumedRoleId")
    arn: str = Field(..., alias="Arn")


class AWSAssumeRoleResponse(BaseModel):
    credentials: AWSCredentials = Field(..., alias="Credentials")
    assumed_role_user: AWSAssumedRoleUser | None = Field(None, alias="AssumedRoleUser")


class AWSRole(BaseModel):
    role_arn: str = Field(..., alias="RoleArn")
    session_name: str = Field(..., alias="SessionName")
    external_id: str = Field(..., alias="ExternalId")


class AWSIdentity(BaseModel):
    user_id: str = Field(..., alias="UserId")
    account_id: str = Field(..., alias="AccountId")
    session_id: str = Field(..., alias="SessionId")
