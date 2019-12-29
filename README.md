# Rainbowterm

Rainbowterm is a tool for managing color themes in [iTerm2][].

Why use Rainbowterm?

- Switch themes with a few keystrokes, quickly finding the one you want.
- Let it choose a theme for you, optimized for ambient conditions.
- Automatically switch themes periodically. _With a fading transition!_

## Install

Install with [Homebrew][]:

1. `brew tap mk12/rainbowterm https://github.com/mk12/rainbowterm`
2. `brew install rainbowterm`

## Usage

Run `rainbowterm help` to see the available commands:

- `rainbowterm` enters interactive mode.
- `rainbowterm set` lets you to switch to a new color theme.
- `rainbowterm list` lists all your color themes (favorites only with `-f`).
- `rainbowterm edit` edits your config file (favorites file with `-f`).

For more information on a command `CMD`, run `rainbowterm help CMD`.

## Getting started

Run `rainbowterm`:

```
j  next               J  next favorite
k  previous           K  previous favorite
p  pick using fzf     f  toggle favorite
l  switch light/dark  s  shuffle
q  quit               i  show info
```

Use <kbd>j</kbd> and <kbd>k</kbd> to go through your themes and instantly apply them. If you have [fzf][], use <kbd>p</kbd> to fuzzy-search.

## Features

Rainbowterm lets you keep track of your favorite themes. View them with `rainbowterm list -f`, edit them with `rainbowterm edit -f`, or choose them in interactive mode by pressing <kbd>f</kbd>. Then, run `rainbowterm set -r` to pick a random one.

Run `rainbowterm set -s` to pick a "smart" favorite. It will be chosen based on (1) the position of the sun, (2) the brightness of your display, and (3) a random factor. The first time, there will be a popup asking if [LocateMe][] can use Location Services. This lets Rainbowterm determine the solar altitude angle for your current location.

Pass the `-a` flag to `rainbowterm set` to transition with a fading animation. It seems to work better when iTerm2's Metal renderer is enabled.

**TODO: automatic cycling**

## Base16

Rainbowterm works great in conjunction with [Base16][]. You can download ~100 great iTerm2 themes from [base16-iterm2][]. If you stick with the ANSI color palette, Rainbowterm's updates can instantly affect all your running programs. See [chriskempson/base16#174](https://github.com/chriskempson/base16/issues/174) for more details.

## Dependencies

These dependencies are automatically installed by Homebrew:

- Python 3.7+
- [iterm2][iterm2-py], the Python library for controlling iTerm2.
- [astral][], a Python library used to calculate sunrise and sunset.
- [dateutil][], a Python library for dealing with dates and times.
- [LocateMe][], a tool for accessing your location.
- [brightness][], a tool for accessing the display brightness.

The following dependencies are optional:

- [fzf][], a fuzzy search tool used in interactive mode.

## Contributing

To hack on Rainbowterm, follow these steps:

1. Clone the repository.
2. (Optional) Set up a virtual environment using  [venv][] or [virtualenv][].
3. Run `make install` to get dependencies and install Rainbowterm in editable mode.

Before committing code, run `make`. This does four things:

1. Formats code with [black][]: `make fmt`.
2. Lints code with [flake8][]: `make lint`.
3. Typechecks code with [mypy][]: `make tc`.
4. Runs tests with [pytest][]: `make test`.

## Changelog

This project has had 3 major iterations:

1. I wrote a super hacky script. It parsed the iTerm2 XML preferences and inserted keybindings for all the color presets. To switch presets for you, it simulated key presses with AppleScript.
2. I discovered [iTerm2's proprietary escape codes][escape] and promply rewrote it to use that. And I implemented the fading animation feature.
3. iTerm2 released the [Python API][python-api], so I had to rewrite it again. This time I split up the giant script into smaller modules.

## License

© 2019 Mitchell Kember

Rainbowterm is available under the MIT License; see [LICENSE](LICENSE.md) for details.

[astral]: https://github.com/sffjunkie/astral
[base16-iterm2]: https://github.com/martinlindhe/base16-iterm2
[Base16]: http://chriskempson.com/projects/base16
[black]: https://black.readthedocs.io/en/stable/
[brightness]: https://github.com/nriley/brightness
[dateutil]: https://github.com/dateutil/dateutil
[escape]: https://www.iterm2.com/documentation-escape-codes.html
[flake8]: http://flake8.pycqa.org/en/latest/
[fzf]: https://github.com/junegunn/fzf
[Homebrew]: https://brew.sh
[iterm2-py]: https://github.com/gnachman/iTerm2/tree/master/api/library/python/iterm2
[iTerm2]: https://iterm2.com
[LocateMe]: https://iharder.sourceforge.io/current/macosx/locateme
[mypy]: http://mypy-lang.org
[pytest]: https://pytest.readthedocs.io/en/latest/
[python-api]: https://www.iterm2.com/python-api/
[venv]: https://docs.python.org/3/library/venv.html
[virtualenv]: https://virtualenv.pypa.io/en/latest/
