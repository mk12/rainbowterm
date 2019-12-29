"""This module provides general utilities."""

import contextlib
import subprocess
import sys
from datetime import datetime

import dateutil.parser
import dateutil.tz

PROGRAM = "rainbowterm"


class FatalError(Exception):
    """An error that causes the program to abort."""

    def __init__(self, message: str):
        """Create a new FatalError with an error message."""
        self.message = message

    def __str__(self) -> str:
        return self.message


@contextlib.contextmanager
def abort_on_fatal_error():
    """Context manager that aborts if it catches a FatalError."""
    try:
        yield
    except FatalError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        sys.exit(1)


def execute(program, args, **kwargs):
    """Executes a command in a subprocess and returns its standard output."""
    try:
        return (
            subprocess.run([program, *args], stdout=subprocess.PIPE, **kwargs)
            .stdout.decode()
            .strip()
        )
    except FileNotFoundError:
        raise FatalError(f"{program} not installed")


def parse_time(time: str) -> datetime:
    """Parse a string as a datetime. Return the current time if it is None."""
    if time is None:
        return datetime.now(dateutil.tz.tzutc())
    try:
        dt = dateutil.parser.parse(time)
        if not dt.tzinfo:
            # Assume the local timezone.
            dt = dt.astimezone()
        return dt
    except ValueError:
        raise FatalError(f"{time}: cannot parse time")
