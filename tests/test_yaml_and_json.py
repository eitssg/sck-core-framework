import pytest

import io
from datetime import datetime, timezone

import core_framework as util


@pytest.fixture(scope="module")
def data_for_testing():
    return {
        "client": "my-client",
        "task": "compile",
        "portfolio": "my-portfolio",
        "app": "my-app",
        "branch": "my-branch",
        "build": "dp-build",
        "automation_type": "deployspec",
        "date1": "2021-01-01",
        "date2": "2021-01-02T01:30:20Z",
        "now": "2025-01-04T13:30:57.921837",
        "then": datetime(2025, 1, 4, 13, 30, 57, 921837),
    }


def test_to_from_yaml(data_for_testing: dict):

    yaml_string = util.to_yaml(data_for_testing)

    assert yaml_string is not None

    assert (
        yaml_string
        == 'client: "my-client"\ntask: "compile"\nportfolio: "my-portfolio"\napp: "my-app"\nbranch: "my-branch"\n'
        'build: "dp-build"\nautomation_type: "deployspec"\ndate1: "2021-01-01"\ndate2: "2021-01-02T01:30:20Z"\n'
        'now: "2025-01-04T13:30:57.921837"\nthen: "2025-01-04T13:30:57.921837"\n'
    )

    data = util.from_yaml(yaml_string)

    date1 = datetime(2021, 1, 1, 0, 0)
    date2 = datetime(2021, 1, 2, 1, 30, 20, tzinfo=timezone.utc)
    now = datetime(2025, 1, 4, 13, 30, 57, 921837)
    then = datetime(2025, 1, 4, 13, 30, 57, 921837)

    assert data is not None

    assert data["date1"] == date1
    assert data["date2"] == date2
    assert data["now"] == now
    assert data["then"] == then


def test_read_write_yaml(data_for_testing: dict):

    stream = io.StringIO()
    util.write_yaml(data_for_testing, stream)
    yaml_string = stream.getvalue()

    assert (
        yaml_string
        == 'client: "my-client"\ntask: "compile"\nportfolio: "my-portfolio"\napp: "my-app"\nbranch: "my-branch"\n'
        'build: "dp-build"\nautomation_type: "deployspec"\ndate1: "2021-01-01"\ndate2: "2021-01-02T01:30:20Z"\n'
        'now: "2025-01-04T13:30:57.921837"\nthen: "2025-01-04T13:30:57.921837"\n'
    )

    stream = io.StringIO(yaml_string)
    data = util.read_yaml(stream)

    date1 = datetime(2021, 1, 1, 0, 0)
    date2 = datetime(2021, 1, 2, 1, 30, 20, tzinfo=timezone.utc)
    now = datetime(2025, 1, 4, 13, 30, 57, 921837)
    then = datetime(2025, 1, 4, 13, 30, 57, 921837)

    assert data is not None

    assert data["date1"] == date1
    assert data["date2"] == date2
    assert data["now"] == now
    assert data["then"] == then


def test_to_from_json(data_for_testing: dict):

    json_string = util.to_json(data_for_testing)

    assert json_string is not None

    assert (
        json_string
        == '{"client": "my-client", "task": "compile", "portfolio": "my-portfolio", "app": "my-app", "branch": "my-branch", '
        '"build": "dp-build", "automation_type": "deployspec", "date1": "2021-01-01", "date2": "2021-01-02T01:30:20Z", '
        '"now": "2025-01-04T13:30:57.921837", "then": "2025-01-04T13:30:57.921837"}'
    )

    data = util.from_json(json_string)

    date1 = datetime(2021, 1, 1, 0, 0)
    date2 = datetime(2021, 1, 2, 1, 30, 20, tzinfo=timezone.utc)
    now = datetime(2025, 1, 4, 13, 30, 57, 921837)
    then = datetime(2025, 1, 4, 13, 30, 57, 921837)

    assert data is not None

    assert data["date1"] == date1
    assert data["date2"] == date2
    assert data["now"] == now
    assert data["then"] == then


def test_read_write_json(data_for_testing: dict):

    stream = io.StringIO()
    util.write_json(data_for_testing, stream)
    json_string = stream.getvalue()

    assert json_string is not None

    assert (
        json_string
        == '{"client": "my-client", "task": "compile", "portfolio": "my-portfolio", "app": "my-app", "branch": "my-branch", '
        '"build": "dp-build", "automation_type": "deployspec", "date1": "2021-01-01", "date2": "2021-01-02T01:30:20Z", '
        '"now": "2025-01-04T13:30:57.921837", "then": "2025-01-04T13:30:57.921837"}'
    )

    stream = io.StringIO(json_string)
    data = util.read_json(stream)

    date1 = datetime(2021, 1, 1, 0, 0)
    date2 = datetime(2021, 1, 2, 1, 30, 20, tzinfo=timezone.utc)
    now = datetime(2025, 1, 4, 13, 30, 57, 921837)
    then = datetime(2025, 1, 4, 13, 30, 57, 921837)

    assert data is not None

    assert data["date1"] == date1
    assert data["date2"] == date2
    assert data["now"] == now
    assert data["then"] == then
