"""This module manages config files and persistent storage."""

import configparser
import operator
import os
import re
from importlib import resources
from pathlib import Path
from typing import Callable, List, Sequence, Set, TypeVar

from rainbowterm.utils import FatalError

# Maximum entries to store in the smart_history file.
MAX_SMART_HISTORY = 100

# Generic type variable.
T = TypeVar('T')


def read_file(path: Path) -> str:
    """Read the contents of a file.

    Strips leading and trailing whitespace from the content.
    """
    with open(path) as file:
        return file.read().strip()


def write_file(path: Path, content: str):
    """Write a string to a file, creating directories if necessary.

    Appends a trailing newline the content.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as file:
        print(content, file=file)


class Paths:
    """Class that produces paths for config and data files."""

    def __init__(self, config_dir: Path, data_dir: Path):
        """Create a new Paths object."""
        self.config_dir = config_dir
        self.data_dir = data_dir

    @staticmethod
    def xdg(subdir: str) -> "Paths":
        """Return an instance following the XDG Base Directory Specification.

        Spec:
        https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html.
        """
        config_base = Path(
            os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        )
        data_base = Path(
            os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")
        )
        return Paths(
            config_dir=config_base / subdir, data_dir=data_base / subdir
        )

    def config(self, name: str) -> Path:
        """Return the path to a config file."""
        return self.config_dir / name

    def data(self, name: str) -> Path:
        """Return the path to a data file."""
        return self.data_dir / name


class Config:
    """Class that holds application configuration."""

    def __init__(self, parser: configparser.ConfigParser):
        """Create a Config object from an already-parsed ConfigParser."""
        assert parser.sections()
        self.parser = parser

    @staticmethod
    def load(paths: Paths) -> "Config":
        """Load config from the filesystem."""
        parser = configparser.ConfigParser()
        # First, load the default config.
        default_path = __package__, "default_config.ini"
        with resources.open_text(*default_path) as file:
            parser.read_file(file)
        # Then, override it with the user config.
        path = paths.config("config.ini")
        if path.exists():
            try:
                parser.read(path)
            except configparser.Error as ex:
                reason = re.sub(r"While reading from[^:]+: ", "", str(ex))
                raise FatalError(f"{path}: malformed config file ({reason})")
        return Config(parser)

    def get(self, section: str, key: str) -> str:
        """Get a string config value."""
        try:
            return self.parser[section][key]
        except configparser.Error:
            raise FatalError(f"failed to get {section}.{key} config")

    def value(
        self, parse: Callable[[str], T], section: str, key: str, **kwargs
    ) -> T:
        """Get a parsed config value."""
        string = self.get(section, key)
        assert string is not None
        try:
            value = parse(string)
            for cmp, x in kwargs.items():
                # Keyword arguments can be lt, gt, le, ge, etc.
                if not getattr(operator, cmp)(value, x):
                    raise ValueError
            return value
        except ValueError:
            raise FatalError(f"{string}: invalid {section}.{key} config")

    def bool(self, section: str, key: str) -> bool:
        """Get a boolean config value."""
        def parse(value: str) -> bool:
            if value.lower() == "true":
                return True
            if value.lower() == "false":
                return False
            raise ValueError
        return self.value(parse, section, key)

    def int(self, *args, **kwargs) -> int:
        """Get an integer config value."""
        return self.value(int, *args, **kwargs)

    def float(self, *args, **kwargs) -> float:
        """Get a floating-point config value."""
        return self.value(float, *args, **kwargs)


class FileStore:
    """Class that provides file-backed properties.

    This class manages 2 files:

        favourites (config file):
            User's favorite color presets.
        smart_history (data file):
            Recent smart-chosen color presets.
    """

    def __init__(self, paths: Paths):
        """Create a new FileStore."""
        self.paths = paths

    @property
    def favorites(self) -> Set[str]:
        path = self.paths.config("favorites")
        if not path.exists():
            return set()
        return set(read_file(path).split())

    @favorites.setter
    def favorites(self, new_favorites: Set[str]):
        path = self.paths.config("favorites")
        write_file(path, "\n".join(sorted(new_favorites)))

    @property
    def smart_history(self) -> List[str]:
        path = self.paths.data("smart_history")
        if not path.exists():
            return []
        return read_file(path).split()

    @smart_history.setter
    def smart_history(self, new_smart_history: Sequence[str]):
        path = self.paths.data("smart_history")
        new_smart_history = new_smart_history[-MAX_SMART_HISTORY:]
        write_file(path, "\n".join(new_smart_history))
