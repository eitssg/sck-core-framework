from unittest.mock import patch
import pytest
import core_logging as log


@pytest.fixture(autouse=True)
def setup_logging():
    log.setup("prn:core:network:master:1")


@pytest.fixture
def mock_format_time():
    with patch("time.strftime") as mock:
        yield mock


def test_status(capsys, mock_format_time):

    mock_format_time.return_value = "2021-07-01 12:00:00"

    log.status("200", "OK", scope="build", details={"item": "a"}, identity="Ident")

    captured = capsys.readouterr()
    assert (
        captured.out
        == "2021-07-01 12:00:00 [Ident] [STATUS] 200 OK (build)\n    item: a\n"
    )

    log.status(
        status_label="200",
        reason="OK",
        scope="build",
        details={"item": "a"},
        identity="Ident",
    )
    captured = capsys.readouterr()
    assert (
        captured.out
        == "2021-07-01 12:00:00 [Ident] [STATUS] 200 OK (build)\n    item: a\n"
    )


def test_warning(capsys, mock_format_time):

    mock_format_time.return_value = "2021-07-01 12:00:00"

    details = {"item": "a"}
    log.warning("Waiting for 2 running action to complete", details, identity="Ident")

    captured = capsys.readouterr()
    assert (
        captured.out
        == "2021-07-01 12:00:00 [Ident] [WARN] Waiting for 2 running action to complete\n    item: a\n"
    )


def test_trace(capsys, mock_format_time):

    mock_format_time.return_value = "2021-07-01 12:00:00"

    log.trace("This a trace message")

    captured = capsys.readouterr()
    assert (
        captured.out
        == "2021-07-01 12:00:00 [prn:core:network:master:1] [TRACE] This a trace message\n"
    )


def test_info(capsys, mock_format_time):

    mock_format_time.return_value = "2021-07-01 12:00:00"

    log.info(
        "Status: %s complete (%s running, %s runnable, %s pending, %s completed, %s incomplete)",
        "10%",
        5,
        10,
        3,
        2,
        1,
        {"RunningActions": ["boo1"], "RunnableActions": ["boo2"]},
    )

    captured = capsys.readouterr()
    assert (
        captured.out == "2021-07-01 12:00:00 [prn:core:network:master:1] [INFO] "
        "Status: 10% complete (5 running, 10 runnable, 3 pending, 2 completed, 1 incomplete)\n"
        "    RunnableActions:\n    - boo2\n"
        "    RunningActions:\n    - boo1\n"
    )


def test_status_with_format(capsys, mock_format_time):

    mock_format_time.return_value = "2021-07-01 12:00:00"

    log.status(
        "RELEASE_IN_PROGRESS",
        "Build release %s",
        "started",
        {"item": 3, "blanked": True},
    )

    captured = capsys.readouterr()
    assert (
        captured.out
        == "2021-07-01 12:00:00 [prn:core:network:master:1] [STATUS] RELEASE_IN_PROGRESS Build release started\n    blanked: true\n    item: 3\n"
    )


def test_msg(capsys, mock_format_time):

    mock_format_time.return_value = "2021-07-01 12:00:00"

    log.msg("Hello there!", identity="my identity")

    captured = capsys.readouterr()

    assert captured.out == "2021-07-01 12:00:00 [my identity] [MSG] Hello there!\n"


def test_debug(capsys, mock_format_time):

    mock_format_time.return_value = "2021-07-01 12:00:00"

    scope = "build"
    prn = "myprn"
    status = "COMPLETED"
    message = "the message is completed"

    log.debug("(API) Setting status of %s '%s' to %s (%s)", scope, prn, status, message)

    captured = capsys.readouterr()
    assert (
        captured.out
        == "2021-07-01 12:00:00 [prn:core:network:master:1] [DEBUG] (API) Setting status of build 'myprn' to COMPLETED (the message is completed)\n"
    )


if __name__ == "__main__":
    pytest.main()
