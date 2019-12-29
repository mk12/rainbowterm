from datetime import datetime

from dateutil.tz import tzutc

import pytest

import rainbowterm.utils as u


def test_abort_on_fatal_error_pass():
    with u.abort_on_fatal_error():
        pass


def test_abort_on_fatal_error_raise_fatal(capsys):
    with pytest.raises(SystemExit):
        with u.abort_on_fatal_error():
            raise u.FatalError("something bad")
    out, err = capsys.readouterr()
    assert "something bad" in err


def test_abort_on_fatal_error_raise_other():
    with pytest.raises(ValueError):
        with u.abort_on_fatal_error():
            raise ValueError


def test_execute():
    assert u.execute("echo", ["hello"]) == "hello"
    assert u.execute("echo", [" hello "]) == "hello"


def test_execute_fail(monkeypatch):
    monkeypatch.setenv("PATH", "")
    with pytest.raises(u.FatalError, match="floof not installed"):
        u.execute("floof", [])


def test_parse_time():
    assert type(u.parse_time(None)) is datetime
    assert u.parse_time("3pm").hour == 15
    assert u.parse_time("2000-01-01T06:00:00Z") == datetime(
        2000, 1, 1, 6, 0, 0, tzinfo=tzutc()
    )


def test_parse_time_fail():
    with pytest.raises(u.FatalError, match="cannot parse time"):
        u.parse_time("asdf")
