import os
from pathlib import Path

import pytest

import rainbowterm.services as s
import rainbowterm.utils as u


LOCATEME_SCRIPT = """\
#!/bin/bash
echo "0.50 0.50"
"""

BRIGHTNESS_SCRIPT = """\
#!/bin/bash
echo "display 0: brightness 0.25"
echo "display 1: brightness 0.50"
"""


def test_geolocation(monkeypatch, tmp_path: Path):
    with open(tmp_path / "locateme", "w") as file:
        print(LOCATEME_SCRIPT, file=file)
    os.chmod(tmp_path / "locateme", 0o0755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert s.geolocation() == (0.5, 0.5)


def test_geolocation_not_installed(monkeypatch):
    monkeypatch.setenv("PATH", "")
    with pytest.raises(u.FatalError, match="locateme"):
        s.geolocation()


def test_display_brightness(monkeypatch, tmp_path: Path):
    with open(tmp_path / "brightness", "w") as file:
        print(BRIGHTNESS_SCRIPT, file=file)
    os.chmod(tmp_path / "brightness", 0o0755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert s.display_brightness(0) == 0.25
    assert s.display_brightness(1) == 0.5
    assert s.display_brightness(2) is None


def test_display_brightness_not_installed(monkeypatch):
    monkeypatch.setenv("PATH", "")
    with pytest.raises(u.FatalError, match="brightness"):
        s.display_brightness(0)
