"""This module implements the application's command-line interface."""

import asyncio
import inspect
import os
import random
import subprocess
import sys
from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta
from typing import Dict, Tuple

from rainbowterm.actions import light_dark
from rainbowterm.files import FileStore, Paths
from rainbowterm.terminal import Profile, Terminal
from rainbowterm.utils import PROGRAM, fail

Args = Namespace


def main():
    """Entry point of the program."""
    parser, commands = get_parser()
    args = parser.parse_args()
    if args.command == "help":
        if args.help_target in commands:
            commands[args.help_target].print_help()
        else:
            parser.print_help()
        return
    if not args.command:
        args.command = "interactive"
    command = globals()[f"command_{args.command}"]
    assert command, "unexpected command name"
    filestore = FileStore(Paths.xdg(PROGRAM))
    if inspect.iscoroutinefunction(command):
        Terminal.run(command, args, filestore)
    else:
        command(args, filestore)


def get_parser() -> Tuple[ArgumentParser, Dict[str, ArgumentParser]]:
    """Create the command-line argument parser."""
    parser = ArgumentParser(
        description="tool for managing color themes in iTerm2"
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
        "-P",
        "--profile",
        nargs="?",
        const="ACTIVE",
        help="modify the current/named profile",
    )
    set_command.add_argument(
        "-e",
        "--escape",
        action="store_true",
        help="use escape codes instead of Python API"
    )
    set_command.add_argument(
        "-a", "--animate", action="store_true", help="animate preset transition"
    )
    set_command.add_argument(
        "-R",
        "--allow-repeat",
        action="store_true",
        help="allow repeats for --random/--smart",
    )
    set_command.add_argument(
        "-t", "--time", help="simulate given time for --smart"
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
    list_group.add_argument(
        "-s",
        "--smart",
        action="store_true",
        help="list 24h of set --smart choices",
    )
    list_command.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show brightness and contrast info",
    )
    list_command.add_argument(
        "-S",
        "--scores",
        action="store_true",
        help="show scores for set --smart",
    )
    list_command.add_argument(
        "-t", "--time", help="simulate given time for --scores"
    )
    edit_command = commands.add_parser("edit", help="edit config file")
    edit_command.add_argument(
        "-f", "--favorites", action="store_true", help="edit favorites file"
    )
    return parser, commands.choices


async def command_interactive(args: Args, fs: FileStore, terminal: Terminal):
    """Enter interactive mode."""
    if not sys.stdin.isatty():
        fail("interactive mode requires a tty")
    Interactive(fs, terminal).run()


async def command_set(args, filestore: FileStore, terminal: Terminal):
    """Set the iTerm2 color preset."""
    all_preset_names = await terminal.all_preset_names()
    current = await terminal.active_preset(Profile.session())
    if not current:
        fail("cannot determine current preset")
    if args.preset:
        if args.preset not in all_preset_names:
            fail(f"{args.preset}: unknown preset", "list")
        preset = args.preset
    elif args.light_dark:
        preset = light_dark(current[0], all_preset_names)
        if not preset:
            fail(f"{current} does not have a light/dark version")
    elif args.random:
        if args.allow_repeat:
            options = list(filestore.favorites)
        else:
            options = list(filestore.favorites - {current})
        if not options:
            fail("need at least 2 favorites to pick a new random preset")
        preset = random.choice(options)
    # elif args.smart:
    #     preset = self.smart_choice(
    #         self.favorites,
    #         score_time=parse_time(args.time),
    #         consider_repetition=not args.allow_repeat,
    #     )
    else:
        # With no arguments, reset the theme (useful if out of sync).
        preset = current

    print(f"setting preset to {preset}")
    if args.animate:
        # self.animate_preset(preset)
        frames = 50
        sleep = 50 / 1000  # convert to milliseconds
        start_scheme = current[1]
        end_scheme = None
        async for name, colors in terminal.all_presets():
            if name == preset:
                end_scheme = colors
                break
        else:
            fail("Canont find colors")
        for i in range(1, frames + 1):
            colors = start_scheme.interpolate(end_scheme, i / frames)
            await terminal.set_colors(Profile.session(), colors)
            print(".", end="", flush=True)
            # await asyncio.sleep(sleep)
        await terminal.set_preset(Profile.session(), preset)
        print()
        pass
    else:
        await terminal.set_preset(Profile.session(), preset)


def command_list(args: Args, fs: FileStore):
    """List color presets, optionally with additional information."""
    # Collect the list of presets based on the arguments.
    lines = None
    if args.current:
        presets = [self.current]
    elif args.favorites:
        presets = sorted(fs.favorites)
    elif args.smart:
        if args.scores:
            # Too confusing: is it scores now, or at that time? Do we sort?
            fail("cannot use --scores with --smart")
        now = datetime.now().astimezone()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        times = [midnight + timedelta(hours=i) for i in range(24)]
        presets = [
            smart_choice(fs.favorites, t, consider_repetition=False)
            for t in times
        ]
        lines = [f"{t}: {preset}" for t, preset in zip(times, presets)]
    else:
        presets = sorted(self.presets)

    # Simple case: just print the lines.
    if not lines:
        lines = presets
    if not (args.verbose or args.scores):
        print("\n".join(lines))
        return

    def verbose_info(preset):
        b = self.presets[preset].get("brightness")
        c = self.presets[preset].get("contrast")
        return [f"brightness={b:.3f}", f"contrast={c:.3f}"]

    def smart_info(score):
        return [f"{key}={val:06.3f}" for key, val in score.items()]

    # Add extra information to all the lines.
    pad = max(len(line) for line in lines)
    pairs = [(p, [f"{line:{pad}}"]) for p, line in zip(presets, lines)]
    if args.verbose:
        # Add brightness and contrast info.
        pairs = [(p, items + verbose_info(p)) for p, items in pairs]
    if args.scores:
        # Add smart scores and sort by descending total score.
        scores = self.smart_scores(presets, parse_time(args.time))
        pairs = [(p, items + smart_info(scores[p])) for p, items in pairs]
        pairs.sort(key=lambda line: scores[line[0]]["total"], reverse=True)
    print("\n".join("  ".join(items) for _, items in pairs))


def command_edit(args: Args, fs: FileStore):
    """Edit one of the configuration files."""
    editor = os.environ.get("VISUAL", os.environ.get("EDITOR"))
    if not editor:
        fail("must set the VISUAL or EDITOR environment variable")
    path = fs.paths.config("favorites" if args.favorites else "config.ini")
    subprocess.run([editor, path])


# def set_preset(preset):
#     """Update the current preset using iTerm2 escape codes."""
#     set_iterm_colors("preset", preset)
#     self.current = preset

