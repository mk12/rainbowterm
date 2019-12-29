"""This module provides access to external services."""

import re
import subprocess
from typing import Optional, Tuple

from rainbowterm.utils import FatalError, execute


def geolocation() -> Tuple[float, float]:
    """Return current (latitude, longitude) using LocateMe."""
    try:
        latitude, longitude = execute("locateme", ["-f", "{LAT} {LON}"]).split()
        return float(latitude), float(longitude)
    except ValueError:
        raise FatalError("failed to parse locateme output")


def display_brightness(display_num: int) -> Optional[float]:
    """Return the brightness of the display as a number between 0 and 1.

    The display_num should be 0 for the primary display and larger numbers for
    others. If there is no brightness information for the display, returns None.
    """
    try:
        output = execute("brightness", ["-l"], stderr=subprocess.DEVNULL)
        pattern = re.compile(f"^display {display_num}: brightness ([0-9.]+)$")
        for line in output.split("\n"):
            match = pattern.search(line)
            if match:
                return float(match.group(1))
        return None
    except ValueError:
        raise FatalError("failed to parse brightness output")
