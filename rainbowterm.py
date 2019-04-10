#!/usr/bin/env python3

"""Tool for managing iTerm2 color presets."""

from datetime import datetime
from pathlib import Path
import argparse
import configparser
import functools
import itertools
import json
import operator
import os
import random
import re
import subprocess
import sys
import termios
import time
import tty
import xml.etree.ElementTree as ET

from astral import Astral
import dateutil.parser
import dateutil.tz


PROGRAM = "rainbowterm"

ITERM2_PREFS_FILE = "com.googlecode.iterm2.plist"

# Color keys accepted by iTerm2's SetColors properietary escape code.
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

# Map from iTerm2 plist keys to COLOR_NAMES.
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

# Dict keys used to represent colors (colorspace and RGB values).
COMPONENT_NAMES = ["cs", "r", "g", "b"]

# Map from iTerm2 plist keys to COMPONENT_NAMES.
PLIST_COMPONENT_KEYS = {
    "Color Space": "cs",
    "Red Component": "r",
    "Green Component": "g",
    "Blue Component": "b",
}

# Menu shown in interactive mode.
INTERACTIVE_MENU = """\
j  next               J  next favorite
k  previous           K  previous favorite
p  pick using fzf     f  toggle favorite
l  switch light/dark  s  shuffle
q  quit
"""

# Maximum entries to store in the smart_history file.
MAX_SMART_HISTORY = 100

# Default configuration values (overriden by config.ini).
DEFAULT_CONFIG = {
    "iterm2": {"prefs": ""},
    "animation": {"frames": 100, "sleep": 50, "reset_delay": 500},
    "smart": {
        "sun_weight": 10,
        "display_weight": 2,
        "random_weight": 1,
        "sun_bimodal": True,
        "sun_offset": 0,
        "sun_min": 0,
        "sun_max": 1,
        "display_number": 0,
        "display_offset": 0,
        "display_min": 0.2,
        "display_max": 0.5,
        "avoid_repeat": 2,
    },
}


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


def clamp(x, lower=0, upper=1):
    """Clamp a value to the given range (by default, 0 to 1)."""
    return max(lower, min(upper, x))


def map_number(x, source, target):
    """Re-maps a number from one range to another, and clamps it."""
    a, b = source
    c, d = target
    result = (x - a) / (b - a) * (d - c) + c
    return clamp(result, c, d)


def color_brightness(color):
    """Calculate the brightness of an RGB color as a value between 0 and 1."""
    r = float(color["r"])
    g = float(color["g"])
    b = float(color["b"])
    if "cs" in color and color["cs"].lower() != "srgb":
        # Generic fallback. https://www.w3.org/TR/AERT/#color-contrast
        return 0.299 * r + 0.587 * g + 0.114 * b

    # Calculate relative luminance for the sRGB color space.
    # https://www.w3.org/TR/WCAG20/#relativeluminancedef
    def f(x):
        if x <= 0.03928:
            return x / 12.92
        return ((x + 0.055) / 1.055) ** 2.4

    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def schemes_are_compatible(scheme1, scheme2):
    """Return true if two schemes have compatible colorspaces."""
    return all(
        scheme1[name]["cs"] == scheme2[name]["cs"]
        for name in COLOR_NAMES
        if name in scheme1 and name in scheme2
    )


def scheme_brightness(scheme):
    """Calculate the brightness of a color scheme as a value from 0 to 1."""
    return color_brightness(scheme["bg"])


def scheme_contrast(scheme):
    """Calculate the contrast of a color scheme as a value from 0 to 1."""
    # https://www.w3.org/TR/WCAG20/#contrast-ratiodef
    b1 = color_brightness(scheme["fg"])
    b2 = color_brightness(scheme["bg"])
    return clamp(((max(b1, b2) + 0.05) / (min(b1, b2) + 0.05) - 1) / 20)


def real_to_hex(real):
    """Convert a real color component to a two-character hexadecimal format."""
    byte = clamp(round(float(real) * 255), 0, 255)
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


def execute(program, args, **kwargs):
    """Executes a command in a subprocess and returns its standard output."""
    try:
        return (
            subprocess.run([program, *args], stdout=subprocess.PIPE, **kwargs)
            .stdout.decode()
            .strip()
        )
    except FileNotFoundError:
        fail(f"{program} not installed")


def parse_time(time_str):
    """Parse a string as a datetime. Return the current time if it is None."""
    if time_str is None:
        return datetime.now(dateutil.tz.tzutc())
    try:
        dt = dateutil.parser.parse(time_str)
        if not dt.tzinfo:
            # Assume the local timezone.
            dt = dt.astimezone()
        return dt
    except ValueError:
        fail(f"{time_str}: cannot parse time")


def geolocation():
    """Return current (latitude, longitude) using LocateMe."""
    try:
        latitude, longitude = execute("locateme", ["-f", "{LAT} {LON}"]).split()
        return float(latitude), float(longitude)
    except ValueError:
        fail("failed to parse locateme output")


def normalized_solar_elevation(date_time):
    """Return the solar elevation as a number from 0 to 1.

    If date_time is naive, it is assumed to be in UTC. The result is 0 for the
    lowest solar elevation (solar midnight), 0.5 for sunset/sunrise, and 1 for
    the highest solar elevation (solar noon).
    """
    latitude, longitude = geolocation()
    astral = Astral()
    elevation = lambda t: astral.solar_elevation(t, latitude, longitude)
    highest = elevation(astral.solar_noon_utc(date_time.date(), longitude))
    lowest = elevation(astral.solar_midnight_utc(date_time.date(), longitude))
    actual = elevation(date_time)
    if actual > 0:
        return map_number(actual, (0, highest), (0.5, 1))
    return map_number(actual, (lowest, 0), (0, 0.5))


def display_brightness(display_num):
    """Return the brightness of the display as a number between 0 and 1.

    The display_num should be 0 for the primary display and larger numbers for
    others. If the display's brightness cannot be determined, returns None.
    """
    try:
        lines = execute("brightness", ["-l"]).split("\n")
        pattern = re.compile(f"^display {display_num}: brightness ([0-9.]+)$")
        for line in lines:
            match = pattern.search(line)
            if match:
                return float(match.group(1))
        return None
    except ValueError:
        fail("failed to parse brightness output")


def normalized_ranks(values, key=None, reverse=False):
    """Calculate the normalized ranks for a set of values."""
    if not values:
        return {}
    if len(values) == 1:
        return {values[0]: 0.5}
    values = sorted(values, key=key, reverse=reverse)
    n = len(values) - 1
    return {x: i / n for i, x in enumerate(values)}


def bimodal_normalized_ranks(values, middle, key=None, reverse=False):
    """Like normalized_ranks, but assumes a bimodal distribution.

    The result has all values below middle assigned ranks from 0 to 0.5, and all
    values above middle assigned ranks from 0.5 to 1.
    """
    if not key:
        key = lambda x: x
    left = [x for x in values if key(x) <= middle]
    right = [x for x in values if key(x) > middle]
    if reverse:
        left, right = right, left
    # Take the average of gaps between ranks from both sides and use that in the
    # middle, so that we don't have both left and right touching at 0.5.
    left_gap = 0.5 / (len(left) - 1) if len(left) > 1 else 0
    right_gap = 0.5 / (len(right) - 1) if len(right) > 1 else 0
    average_gap = (left_gap + right_gap) / 2
    half_gap = average_gap / 2
    left_ranks = {
        x: map_number(rank, (0, 1), (0, 0.5 - half_gap))
        for x, rank in normalized_ranks(left, key=key, reverse=reverse).items()
    }
    right_ranks = {
        x: map_number(rank, (0, 1), (0.5 + half_gap, 1))
        for x, rank in normalized_ranks(right, key=key, reverse=reverse).items()
    }
    return {**left_ranks, **right_ranks}


def closeness(x, y):
    """Calculate a statistic representing how close x and y are.

    Assumes x and y are between 0 and 1. The result is 1 if x and y are the
    same, 0 if they are as far apart as possible, and in between otherwise.
    """
    return clamp(1 - (x - y) ** 2)


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
        # Cache used by @reader and @writer.
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
        for preset in favorites:
            if preset not in self.presets:
                fail(f"{preset}: invalid preset in favorites", "edit -f")
        return favorites

    @writer(favorites)
    def favorites(self, new_favorites):
        write_file(config_file("favorites"), "\n".join(sorted(new_favorites)))

    @reader
    def smart_history(self):
        path = data_file("smart_history")
        if not path.exists():
            return []
        return read_file(path).split()

    @writer(smart_history)
    def smart_history(self, new_smart_history):
        # Drop elements from the front if it gets too long.
        new_smart_history = new_smart_history[-MAX_SMART_HISTORY:]
        write_file(data_file("smart_history"), "\n".join(new_smart_history))

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
            fail(f"{path}: malformed config file ({reason})")
        return config

    def config_string(self, section, key):
        """Returns a string from the config file."""
        try:
            return self.config[section][key]
        except KeyError:
            return DEFAULT_CONFIG[section][key]

    def config_bool(self, section, key):
        """Returns a boolean from the config file."""
        try:
            # Handles 0, false, no, off, 1, true, yes, on, etc.
            return self.config.getboolean(section, key)
        except configparser.NoOptionError:
            return DEFAULT_CONFIG[section][key]

    def config_value(self, parse, section, key, **kwargs):
        """Returns a parsed value from the config file."""
        string = self.config_string(section, key)
        assert string is not None
        try:
            value = parse(string)
            for cmp, x in kwargs.items():
                # Keyword arguments can be lt, gt, le, ge, etc.
                if not getattr(operator, cmp)(value, x):
                    raise ValueError
            return value
        except ValueError:
            fail(f"{string}: invalid {section}.{key} config")

    def config_int(self, *args, **kwargs):
        return self.config_value(int, *args, **kwargs)

    def config_float(self, *args, **kwargs):
        return self.config_value(float, *args, **kwargs)

    def set_preset(self, preset):
        """Update the current preset using iTerm2 escape codes."""
        set_iterm_colors("preset", preset)
        self.current = preset

    def animate_preset(self, preset):
        """Update the current preset using a fading animation."""
        frames = self.config_int("animation", "frames", gt=0)
        sleep = self.config_float("animation", "sleep", ge=0)
        reset_delay = self.config_float("animation", "reset_delay", ge=0)
        sleep /= 1000  # convert to milliseconds
        start_scheme = self.presets[self.current]
        end_scheme = self.presets[preset]
        if not schemes_are_compatible(start_scheme, end_scheme):
            fail("{self.current} to {preset}: incompatible colorspaces")
        for i in range(1, frames + 1):
            for name in COLOR_NAMES:
                if name not in start_scheme or name not in end_scheme:
                    continue
                start = start_scheme[name]
                end = end_scheme[name]
                color = interpolate_color(start, end, i / frames)
                set_iterm_colors(name, hex_color_value(color))
            print(".", end="", flush=True)
            time.sleep(sleep)
        self.set_preset(preset)
        print()
        # In case it messed up, reset the theme again after a delay.
        if reset_delay > 0:
            time.sleep(reset_delay / 1000)
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

    def smart_scores(self, presets, score_time):
        """Calculate components of scores for smart_choice."""
        # Get the weight for each part of the score.
        parts = "sun", "display", "random"
        weights = {p: self.config_float("smart", f"{p}_weight") for p in parts}

        # Rank presets from 0 to 1 on brightness and contrast values. We leave
        # sun_ranks sorted so that high sun altitude is related to high preset
        # brightness, and reverse display_ranks so that high display brightness
        # is related to low preset contrast.
        if self.config_bool("smart", "sun_bimodal"):
            sun_ranks = bimodal_normalized_ranks(
                presets, middle=0.5, key=lambda p: self.presets[p]["brightness"]
            )
        else:
            sun_ranks = normalized_ranks(
                presets, key=lambda p: self.presets[p]["brightness"]
            )
        display_ranks = normalized_ranks(
            presets, key=lambda p: self.presets[p]["contrast"], reverse=True
        )

        def calculate_ideal_rank(name, base_value):
            """Calculate the ideal rank (that would get the best score)."""
            offset = self.config_float("smart", f"{name}_offset")
            source_range = (
                self.config_float("smart", f"{name}_min", ge=0, le=1),
                self.config_float("smart", f"{name}_max", ge=0, le=1),
            )
            if base_value is None:
                return None
            return map_number(clamp(base_value + offset), source_range, (0, 1))

        # Calculate the ideal values for sun and display ranks.
        ideal_sun_rank = calculate_ideal_rank(
            "sun", normalized_solar_elevation(score_time)
        )
        display_num = self.config_int("smart", "display_number", ge=0)
        ideal_display_rank = calculate_ideal_rank(
            "display", display_brightness(display_num)
        )

        def score(preset):
            """Calculate a score for choosing the preset (higher is better)."""
            sun_rank = sun_ranks[preset]
            display_rank = display_ranks[preset]
            terms = {p: 0 for p in parts}
            if ideal_sun_rank is not None:
                terms["sun"] = closeness(sun_rank, ideal_sun_rank)
            if ideal_display_rank is not None:
                terms["display"] = closeness(display_rank, ideal_display_rank)
            terms["random"] = random.random()
            score = {p: weights[p] * terms[p] for p in parts}
            score["total"] = sum(score.values())
            return score

        return {p: score(p) for p in presets}

    def smart_choice(self, presets, score_time, consider_repetition):
        """Choose a preset with the highest smart score."""
        assert presets
        avoid_repeat = 0
        if consider_repetition:
            avoid_repeat = self.config_int(
                "smart", "avoid_repeat", ge=0, le=MAX_SMART_HISTORY
            )
        # If avoid_repeat is N, do not consider the last N smart choices.
        if avoid_repeat == 0:
            options = presets
        else:
            avoid = set(self.smart_history[-avoid_repeat:])
            options = [p for p in presets if p not in avoid]
        if not options:
            fail("{avoid_repeat}: cannot satisfy smart.avoid_repeat config")
        # Choose the preset with the highest smart score.
        scores = self.smart_scores(options, score_time)
        choice = max(options, key=lambda p: scores[p]["total"])
        self.smart_history += [choice]
        return choice

    def command_list(self, args):
        """List color presets, optionally with additional information."""
        if args.current:
            presets = [self.current]
        elif args.favorites:
            presets = sorted(self.favorites)
        else:
            presets = sorted(self.presets)

        if not (args.verbose or args.smart):
            print("\n".join(presets))
            return

        def verbose_info(preset):
            b = self.presets[preset].get("brightness")
            c = self.presets[preset].get("contrast")
            return [f"brightness={b:4.3f}", f"contrast={c:4.3f}"]

        def smart_info(preset, score):
            return [f"{key}={val:4.3f}" for key, val in score.items()]

        pad = max(len(s) for s in presets)
        lines = [(p, [f"{p:{pad}}"]) for p in presets]
        if args.verbose:
            # Add brightness and contrast info.
            lines = [(p, items + verbose_info(p)) for p, items in lines]
        if args.smart:
            # Add smart scores and sort by descending total score.
            scores = self.smart_scores(presets, parse_time(args.time))
            lines = [
                (p, items + smart_info(p, scores[p])) for p, items in lines
            ]
            lines.sort(key=lambda line: scores[line[0]]["total"], reverse=True)
        print("\n".join("  ".join(items) for _, items in lines))

    def command_edit(self, args):
        """Edit one of the configuration files."""
        editor = os.environ.get("VISUAL", os.environ.get("EDITOR"))
        if not editor:
            fail("must set the VISUAL or EDITOR environment variable")
        path = config_file("favorites" if args.favorites else "config.ini")
        subprocess.run([editor, path])

    def command_set(self, args):
        """Set the iTerm2 color preset."""
        if args.preset:
            if args.preset not in self.presets:
                fail(f"{args.preset}: unknown preset", "list")
            preset = args.preset
        elif args.light_dark:
            preset = self.light_dark(self.current)
            if not preset:
                fail(f"{self.current} does not have a light/dark version")
        elif args.random:
            if args.allow_repeat:
                options = list(self.favorites)
            else:
                options = list(self.favorites - {self.current})
            if not options:
                fail("need at least 2 favorites to pick a new random preset")
            preset = random.choice(options)
        elif args.smart:
            preset = self.smart_choice(
                self.favorites,
                score_time=parse_time(args.time),
                consider_repetition=not args.allow_repeat,
            )
        else:
            # With no arguments, reset the theme (useful if out of sync).
            preset = self.current

        print(f"setting preset to {preset}")
        if args.animate:
            self.animate_preset(preset)
        else:
            self.set_preset(preset)

    def command_interactive(self, args):
        """Enter interactive mode."""
        if not sys.stdin.isatty():
            fail("interactive mode requires a tty")
        Interactive(self).run()

    def command_load(self, args):
        """Load custom color presets from the iTerm2 plist."""
        plist = args.file
        if not plist:
            prefs = self.config_string("iterm2", "prefs")
            if prefs:
                plist = Path(prefs).expanduser() / ITERM2_PREFS_FILE
            else:
                fail("must specify plist file with --file")
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
            scheme = {}
            for color_key, node in plist_iter(node):
                components = {}
                for component_key, node in plist_iter(node):
                    components[PLIST_COMPONENT_KEYS[component_key]] = node.text
                scheme[PLIST_COLOR_KEYS[color_key]] = components
            scheme["brightness"] = scheme_brightness(scheme)
            scheme["contrast"] = scheme_contrast(scheme)
            presets[preset_key] = scheme
        self.presets = presets
        print(f"loaded {len(presets)} presets")


class Interactive:

    """Interactive mode for Rainbowterm."""

    def __init__(self, rainbow):
        self.rainbow = rainbow
        self.preset_list = list(rainbow.presets.keys())
        self.index = self.preset_list.index(rainbow.current)
        self.fzf_input = "\n".join(self.preset_list).encode()
        self.info_str = None

    @property
    def current(self):
        return self.preset_list[self.index]

    @current.setter
    def current(self, new_current):
        self.index = self.preset_list.index(new_current)

    def run(self):
        """Run the interactive mode loop."""
        print(INTERACTIVE_MENU)
        self.print_status()
        while True:
            try:
                char = read_char()
                print("\r\x1b[2K", end="")
            except KeyboardInterrupt:
                break
            if char in ("q", "Q"):
                break
            changed = self.dispatch(char)
            if changed:
                self.rainbow.set_preset(self.current)
            self.print_status()
        self.print_status(end="\n")

    def dispatch(self, char):
        """Dispatch a command by the character the user typed."""
        rainbow = self.rainbow
        if char in ("j", " ", "\n"):
            self.next()
        elif char == "k":
            self.prev()
        elif char == "J":
            if not rainbow.favorites:
                self.info("no favorites")
                return False
            self.next()
            while self.current not in rainbow.favorites:
                self.next()
        elif char == "K":
            if not rainbow.favorites:
                self.info("no favorites")
                return False
            self.prev()
            while self.current not in rainbow.favorites:
                self.prev()
        elif char == "s":
            random.shuffle(self.preset_list)
            self.info("shuffled")
        elif char == "p":
            return self.pick_with_fzf()
        elif char == "l":
            other = rainbow.light_dark(self.current)
            if not other:
                self.info("no light/dark version")
                return False
            self.current = other
        elif char == "f":
            if self.current in rainbow.favorites:
                rainbow.favorites -= {self.current}
                self.info("unfavorited")
            else:
                rainbow.favorites |= {self.current}
                self.info("favorited")
            return False
        else:
            return False
        return True

    def next(self):
        """Advance to the next preset in the list."""
        self.index += 1
        self.index %= len(self.preset_list)

    def prev(self):
        """Go back to the previous preset in the list."""
        self.index -= 1
        self.index %= len(self.preset_list)

    def pick_with_fzf(self):
        """Pick a preset using fzf."""
        try:
            self.current = execute("fzf", [], input=self.fzf_input)
            return True
        except ValueError:
            self.info("invalid selection")
            return False

    def info(self, message):
        """Record an info message to show in the status."""
        self.info_str = message

    def print_status(self, end=""):
        """Print the current status, overwriting the old one."""
        extra = f" ({self.info_str})" if self.info_str else ""
        star = "*" if self.rainbow.current in self.rainbow.favorites else ""
        print(
            f"\r\x1b[2K[{self.index}{star}] {self.current}{extra}",
            end=end,
            flush=True,
        )
        self.info_str = None


def get_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="tool for managing iTerm2 color presets"
    )
    commands = parser.add_subparsers(metavar="command", dest="command")
    help_target = commands.add_parser(
        "help", help="show this help message and exit"
    )
    help_target.add_argument(
        metavar="command",
        dest="help_target",
        nargs="?",
        help="get help for a specific command",
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
    set_command.add_argument(
        "-t", "--time", help="simulate given time for --smart"
    )
    set_command.add_argument(
        "-R",
        "--allow-repeat",
        action="store_true",
        help="allow repeats for -r/-s",
    )
    list_command = commands.add_parser("list", help="list color presets")
    list_group = list_command.add_mutually_exclusive_group()
    list_group.add_argument(
        "-c",
        "--current",
        action="store_true",
        help="list only the current preset",
    )
    list_group.add_argument(
        "-f",
        "--favorites",
        action="store_true",
        help="list only favorite presets",
    )
    list_command.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show brightness and contrast info",
    )
    list_command.add_argument(
        "-s", "--smart", action="store_true", help="show scores for set --smart"
    )
    list_command.add_argument(
        "-t", "--time", help="simulate given time for --smart"
    )
    load_command = commands.add_parser("load", help="load iTerm2 presets")
    load_command.add_argument(
        "-f", "--file", help="specify iTerm2 plist file (XML, not binary)"
    )
    edit_command = commands.add_parser("edit", help=f"edit {PROGRAM} config")
    edit_command.add_argument(
        "-f", "--favorites", action="store_true", help="edit favorites file"
    )
    return parser, commands.choices


def main():
    """Entry point of the program."""
    parser, commands = get_parser()
    args = parser.parse_args()
    if args.command == "help":
        if args.help_target:
            commands[args.help_target].print_help()
        else:
            parser.print_help()
    else:
        if not args.command:
            args.command = "interactive"
        Rainbowterm().run(args)


if __name__ == "__main__":
    main()
