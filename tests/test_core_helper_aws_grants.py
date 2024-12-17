import pytest

import core_helper.aws as aws

import logging

logging.basicConfig(level=logging.DEBUG)

username = "bob"
role_name = "core-automation-admin"


@pytest.fixture
def real_aws(pytestconfig):
    return pytestconfig.getoption("--real-aws")


def test_grants(real_aws):

    # I really don't have a good way to test this without a real AWS account
    if not real_aws:
        return

    try:
        identity = aws.get_identity()

        assert identity is not None

    except Exception as e:
        assert False, str(e)

    account_id = identity["Account"]

    try:
        aws.grant_assume_role_permission(username, role_name, account_id)

    except Exception as e:
        assert False, str(e)

    try:
        aws.revoke_assume_role_permission(username, role_name, account_id)

    except Exception as e:
        assert False, str(e)
