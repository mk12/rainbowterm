#!/usr/bin/env python3

"""Tool for managing iTerm2 color presets."""

from pathlib import Path
import argparse
import configparser
import functools
import itertools
import json
import os
import random
import subprocess
import sys
import termios
import time
import tty
import xml.etree.ElementTree as ET


PROGRAM = "rainbowterm"

ITERM2_PREFS_FILE = "com.googlecode.iterm2.plist"

COLOR_NAMES = [
    "fg",
    "bg",
    "bold",
    "link",
    "selbg",
    "selfg",
    "curbg",
    "curfg",
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "br_black",
    "br_red",
    "br_green",
    "br_yellow",
    "br_blue",
    "br_magenta",
    "br_cyan",
    "br_white",
]

PLIST_COLOR_KEYS = {
    "Foreground Color": "fg",
    "Background Color": "bg",
    "Bold Color": "bold",
    "Link Color": "link",
    "Selection Color": "selbg",
    "Selected Text Color": "selfg",
    "Cursor Color": "curbg",
    "Cursor Text Color": "curfg",
    "Ansi 0 Color": "black",
    "Ansi 1 Color": "red",
    "Ansi 2 Color": "green",
    "Ansi 3 Color": "yellow",
    "Ansi 4 Color": "blue",
    "Ansi 5 Color": "magenta",
    "Ansi 6 Color": "cyan",
    "Ansi 7 Color": "white",
    "Ansi 8 Color": "br_black",
    "Ansi 9 Color": "br_red",
    "Ansi 10 Color": "br_green",
    "Ansi 11 Color": "br_yellow",
    "Ansi 12 Color": "br_blue",
    "Ansi 13 Color": "br_magenta",
    "Ansi 14 Color": "br_cyan",
    "Ansi 15 Color": "br_white",
}

COMPONENT_NAMES = ["cs", "r", "g", "b"]

PLIST_COMPONENT_KEYS = {
    "Color Space": "cs",
    "Red Component": "r",
    "Green Component": "g",
    "Blue Component": "b",
}

INTERACTIVE_MENU = """\
j  next
k  previous
s  shuffle
p  pick using fzf
l  switch light/dark
f  toggle favorite
q  quit
"""

# Animation parameters.
DEFAULT_FRAMES = 100
DEFAULT_SLEEP = 50


def fail(message, try_cmd=""):
    """Print an error message and abort the program."""
    if try_cmd:
        try_cmd = f" (try '{sys.argv[0]} {try_cmd}')"
    print(f"{PROGRAM}: {message}{try_cmd}", file=sys.stderr)
    sys.exit(1)


def config_file(name):
    """Return the path to a config file."""
    var = os.environ.get("XDG_CONFIG_HOME")
    home = Path(var) if var else Path.home() / ".config"
    return home / PROGRAM / name


def data_file(name):
    """Return the path to a data file."""
    var = os.environ.get("XDG_DATA_HOME")
    home = Path(var) if var else Path.home() / ".local/share"
    return home / PROGRAM / name


def read_file(path):
    """Read the contents of a file."""
    with open(path) as file:
        return file.read().strip()


def write_file(path, content):
    """Write a string to a file, creating directories if necessary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as file:
        print(content, file=file)


def plist_iter(nodes):
    """Iterate over plist key-value pairs given an XML node iterator."""
    n = iter(nodes)
    for key, value in iter((lambda: tuple(itertools.islice(n, 2))), ()):
        assert key.tag == "key"
        yield key.text.strip(), value


def real_to_hex(real):
    """Convert a real color component to a two-character hexadecimal format."""
    byte = max(0, min(255, round(float(real) * 255.0)))
    return f"{byte:02x}"


def hex_color_value(color):
    """Convert a color dict to the cs:RRGGBB hexadecimal format."""
    cs = color["cs"]
    rr = real_to_hex(color["r"])
    gg = real_to_hex(color["g"])
    bb = real_to_hex(color["b"])
    return f"{cs}:{rr}{gg}{bb}"


def interpolate_real(r1, r2, t):
    """Linearly interpolate between two real color components."""
    r1 = float(r1)
    r2 = float(r2)
    return r1 + t * (r2 - r1)


def interpolate_color(color1, color2, t):
    """Linearly interpolate between two colors."""
    assert color1["cs"] == color2["cs"]
    return {
        "cs": color1["cs"],
        "r": interpolate_real(color1["r"], color2["r"], t),
        "g": interpolate_real(color1["g"], color2["g"], t),
        "b": interpolate_real(color1["b"], color2["b"], t),
    }


def set_iterm_colors(key, value):
    """Print an iTerm2 escape code to update color settings."""
    msg = f"\x1B]1337;SetColors={key}={value}\x07"
    if "TMUX" in os.environ:
        msg = f"\x1BPtmux;\x1B{msg}\x1B\\"
    print(msg, end="", flush=True)


def read_char():
    """Read a single character from stdin (without pressing enter)."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def reader(f):
    """Decorator for a property getter that reads from disk."""
    key = f.__name__

    @functools.wraps(f)
    def wrapped(self):
        if key not in self.cache:
            self.cache[key] = f(self)
        return self.cache[key]

    return property(wrapped)


def writer(prop):
    """Decorator for a property setter that writes to disk."""

    def decorator(f):
        key = f.__name__

        @functools.wraps(f)
        def wrapped(self, value):
            f(self, value)
            self.cache[key] = value

        return prop.setter(wrapped)

    return decorator


class Rainbowterm:

    """Implementation of Rainbowterm commands."""

    def __init__(self):
        self.cache = {}

    def run(self, args):
        """Run a command given the parsed arguments."""
        command = getattr(self, f"command_{args.command}")
        assert command, "unexpected command name"
        command(args)

    @reader
    def current(self):
        path = data_file("current")
        current = read_file(path) if path.exists() else None
        if not current:
            fail("current preset unknown", "set -p PRESET")
        return current

    @writer(current)
    def current(self, new_current):
        assert new_current in self.presets
        write_file(data_file("current"), new_current)

    @reader
    def presets(self):
        path = data_file("presets")
        if not path.exists():
            fail(f"presets not found", "load")
        presets = json.loads(read_file(path))
        if not presets:
            fail(f"presets are empty", "load")
        return presets

    @writer(presets)
    def presets(self, new_presets):
        write_file(data_file("presets"), json.dumps(new_presets))

    @reader
    def favorites(self):
        path = config_file("favorites")
        if not path.exists():
            fail("favorites not found", "edit -f")
        favorites = set(read_file(path).split())
        if not favorites:
            fail("favorites are empty", "edit -f")
        return favorites

    @writer(favorites)
    def favorites(self, new_favorites):
        write_file(config_file("favorites"), "\n".join(sorted(new_favorites)))

    @reader
    def config(self):
        path = config_file("config.ini")
        if not path.exists():
            return {}
        config = configparser.ConfigParser()
        try:
            config.read(path)
        except configparser.Error as ex:
            reason = ex.message.split()[0]
            fail("{path}: malformed config file ({reason})")
        return config

    def config_string(self, section, key):
        """Returns a string from the config file."""
        try:
            return self.config[section][key]
        except KeyError:
            return None

    def config_int(self, section, key):
        """Returns an int from the config file."""
        value = self.config_string(section, key)
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def set_preset(self, preset):
        """Update the current preset using iTerm2 escape codes."""
        set_iterm_colors("preset", preset)
        self.current = preset

    def animate_preset(self, preset):
        """Update the current preset using a fading animation."""
        frames = self.config_int("animation", "frames") or DEFAULT_FRAMES
        sleep = self.config_int("animation", "sleep") or DEFAULT_SLEEP
        if frames <= 0:
            fail(f"{frames}: invalid animation.frames config")
        if sleep < 0:
            fail(f"{sleep}: invalid animation.sleep config")
        sleep /= 1000.0
        start = self.presets[self.current]
        end = self.presets[preset]
        for i in range(1, frames + 1):
            for name in start:
                start_color = start[name]
                end_color = end[name]
                color = interpolate_color(start_color, end_color, i / frames)
                set_iterm_colors(name, hex_color_value(color))
            print(".", end="", flush=True)
            time.sleep(sleep)
        self.set_preset(preset)
        print()
        # In case it messed up:
        time.sleep(0.5)
        self.set_preset(preset)

    def light_dark(self, preset):
        """Return the corresponding light/dark preset, or None."""
        assert preset in self.presets
        for a, b in [("light", "dark"), ("dark", "light")]:
            for c in [a, "-" + a]:
                for d in [b, "-" + b]:
                    for replacement in [(c, ""), (c, d)]:
                        other = preset.replace(*replacement)
                        if other != preset and other in self.presets:
                            return other
        return None

    def command_list(self, args):
        if args.favorites:
            print("\n".join(self.favorites))
        else:
            print("\n".join(self.presets.keys()))

    def command_edit(self, args):
        editor = os.environ.get("VISUAL", os.environ.get("EDITOR"))
        if not editor:
            fail("must set the VISUAL or EDITOR environment variable")
        path = config_file("favorites" if args.favorites else "config.ini")
        subprocess.run([editor, path])

    def command_set(self, args):
        if args.preset:
            if args.preset not in self.presets:
                fail(f"{args.preset}: unknown preset", "list")
            preset = args.preset
        elif args.light_dark:
            preset = self.light_dark(self.current)
            if not preset:
                fail(f"{self.current} does not have a light/dark version")
        elif args.random:
            options = [p for p in self.favorites if p != self.current]
            # Handle the case where favorites == [current].
            preset = random.choice(options) if options else self.current
        elif args.smart:
            # TODO make it smarter based on time, ambient light
            options = [p for p in self.favorites if p != self.current]
            preset = random.choice(options) if options else self.current
        else:
            # With no arguments, reset the theme (useful if out of sync).
            preset = self.current
        if args.animate:
            self.animate_preset(preset)
        else:
            self.set_preset(preset)

    def command_interactive(self, args):
        if not sys.stdin.isatty():
            fail("interactive mode requires a tty")
        print(INTERACTIVE_MENU)
        preset_list = list(self.presets.keys())
        fzf_input = "\n".join(preset_list).encode()
        index = preset_list.index(self.current)
        message = None

        def print_status(end=""):
            nonlocal index
            nonlocal message
            extra = f" ({message})" if message else ""
            star = "*" if self.current in self.favorites else ""
            print(
                f"\r\x1b[2K[{index}{star}] {self.current}{extra}",
                end=end,
                flush=True,
            )

        print_status()
        while True:
            try:
                char = read_char()
                print("\r\x1b[2K", end="")
            except KeyboardInterrupt:
                break
            message = None
            changed = True
            if char in ("j", " ", "\n"):
                index = (index + 1) % len(preset_list)
            elif char == "k":
                index = (index - 1) % len(preset_list)
            elif char == "s":
                random.shuffle(preset_list)
                message = "shuffled"
            elif char == "p":
                try:
                    preset = (
                        subprocess.run(
                            ["fzf"], input=fzf_input, stdout=subprocess.PIPE
                        )
                        .stdout.decode()
                        .strip()
                    )
                    index = preset_list.index(preset)
                except FileNotFoundError:
                    message = "fzf not installed"
                except ValueError:
                    message = f"invalid selection"
            elif char == "l":
                other = self.light_dark(preset_list[index])
                if other:
                    index = preset_list.index(other)
                else:
                    message = "no light/dark version"
            elif char == "f":
                if self.current in self.favorites:
                    self.favorites -= {self.current}
                    message = "unfavorited"
                else:
                    self.favorites |= {self.current}
                    message = "favorited"
                changed = False
            elif char == "q":
                break
            self.set_preset(preset_list[index])
            print_status()
        print_status(end="\n")

    def command_load(self, args):
        plist = args.file or self.config_string("iterm2", "prefs")
        if not plist:
            fail("must specify plist file with --file")
        plist = Path(plist).expanduser() / ITERM2_PREFS_FILE
        if not plist.exists():
            fail(f"{plist}: file not found")
        with open(plist) as file:
            # There is a null byte for "HotKey Characters" for some reason.
            xml = file.read().replace("\x00", "")
        try:
            root = ET.fromstring(xml).find("dict")
        except ET.ParseError:
            fail(f"{plist}: failed to parse XML")
        preset_root = None
        for key, node in plist_iter(root):
            if key == "Custom Color Presets":
                preset_root = node
                break
        if not preset_root:
            fail(f"{plist}: could not find custom presets")
        presets = {}
        for preset_key, node in plist_iter(preset_root):
            colors = {}
            for color_key, node in plist_iter(node):
                components = {}
                for component_key, node in plist_iter(node):
                    components[PLIST_COMPONENT_KEYS[component_key]] = node.text
                colors[PLIST_COLOR_KEYS[color_key]] = components
            presets[preset_key] = colors
        self.presets = presets
        print(f"loaded {len(presets)} presets")


def get_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="tool for managing iTerm2 color presets"
    )
    commands = parser.add_subparsers(metavar="command", dest="command")
    help_command = commands.add_parser(
        "help", help="show this help message and exit"
    )
    set_command = commands.add_parser("set", help="set the color preset")
    set_group = set_command.add_mutually_exclusive_group()
    set_group.add_argument("-p", "--preset", help="specify a color preset")
    set_group.add_argument(
        "-r", "--random", action="store_true", help="pick a random favorite"
    )
    set_group.add_argument(
        "-s",
        "--smart",
        action="store_true",
        help="pick a smart-random favorite",
    )
    set_group.add_argument(
        "-l",
        "--light-dark",
        action="store_true",
        help="switch between light/dark",
    )
    set_command.add_argument(
        "-a", "--animate", action="store_true", help="animate preset transition"
    )
    list_command = commands.add_parser("list", help="list color presets")
    list_command.add_argument(
        "-f",
        "--favorites",
        action="store_true",
        help="list only favorite presets",
    )
    load_command = commands.add_parser("load", help="load iTerm2 presets")
    load_command.add_argument("-f", "--file", help="specify iTerm2 plist file")
    edit_command = commands.add_parser("edit", help=f"edit {PROGRAM} config")
    edit_command.add_argument(
        "-f", "--favorites", action="store_true", help="edit favorites file"
    )
    return parser


def main():
    """Entry point of the program."""
    parser = get_parser()
    args = parser.parse_args()
    if args.command == "help":
        parser.print_help()
        return
    if not args.command:
        args.command = "interactive"
    Rainbowterm().run(args)


if __name__ == "__main__":
    main()
