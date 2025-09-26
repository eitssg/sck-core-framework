from typing import Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CommonBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    def model_dump(self, **kwargs) -> dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


class PolicyArn(CommonBaseModel):

    arn: str = Field(..., alias='arn')


class Tag(CommonBaseModel):

    key: str = Field(..., alias='Key')
    value: str = Field(..., alias='Value')


class ProvidedContext(CommonBaseModel):

    provider_arn: str = Field(..., alias='ProviderArn')
    context_assertion: str = Field(..., alias='ContextAssertion')


class AssumeRoleRequest(CommonBaseModel):

    role_arn: str = Field(..., alias='RoleArn')
    role_session_name: str = Field(..., alias='RoleSessionName')
    policy_arns: Optional[List[PolicyArn]] = Field(None, alias='PolicyArns')
    policy: Optional[str] = Field(None, alias='Policy')
    duration_seconds: Optional[int] = Field(None, alias='DurationSeconds')
    tags: Optional[List[Tag]] = Field(None, alias='Tags')
    transitive_tag_keys: Optional[List[str]] = Field(None, alias='TransitiveTagKeys')
    external_id: Optional[str] = Field(None, alias='ExternalId')
    serial_number: Optional[str] = Field(None, alias='SerialNumber')
    token_code: Optional[str] = Field(None, alias='TokenCode')
    source_identity: Optional[str] = Field(None, alias='SourceIdentity')
    provided_contexts: Optional[List[ProvidedContext]] = Field(None, alias='ProvidedContexts')


class AssumeRoleResponse(CommonBaseModel):

    access_key_id: str = Field(..., alias='AccessKeyId')
    secret_access_key: str = Field(..., alias='SecretAccessKey')
    session_token: str = Field(..., alias='SessionToken')
    expiration: str = Field(..., alias='Expiration')
    packed_policy_size: int = Field(..., alias='PackedPolicySize')


class AwsCredentials(CommonBaseModel):

    access_key_id: str = Field(..., alias='AccessKeyId')
    secret_access_key: str = Field(..., alias='SecretAccessKey')
    session_token: Optional[str] = Field(None, alias='SessionToken')
    expiration: Optional[datetime] = Field(None, alias='Expiration')
