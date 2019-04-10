# Rainbowterm

Rainbowterm is a tool for managing color schemes in [iTerm2][i2].

Why use Rainbowterm?

- You like changing your color scheme often.
- You want it to be as easy as possible.

Here are its coolest features:

- Switch to a new color scheme with [fzf][fzf].
- Transition between themes with a fading animation.
- Automatically pick themes based on time of day and display brightness.

## Install

Install with [Homebrew][hb]:

1. `brew tap mk12/rainbowterm https://github.com/mk12/rainbowterm`
2. `brew install rainbowterm`

## Usage

Run `rainbowterm help` to see the available commands:

- `rainbowterm` with no arguments enters interactive mode.
- `rainbowterm set` allows you to switch to a new color preset.
- `rainbowterm edit` edits your config file (favorites file with `-f`).
- `rainbowterm list` lists all your color presets (favorites only with `-f`).
- `rainbowterm load` loads color presets from iTerm2 preferences.

For more information on a particular command `CMD`, run `rainbowterm help CMD`.

## Getting started

First, make sure you enable _"Load preferences from a custom folder or URL"_ in your iTerm2 preferences. If you have a dotfiles repository, I recommend storing it there. Then, run `rainbowterm edit` to edit `~/.config/rainbowterm/config.ini`, and enter the path you just chose:

```ini
[iterm2]
prefs = /path/to/your/iterm2/prefs
# For example, mine is ~/GitHub/dotfiles/iterm2
```

Next, run `rainbowterm load` to parse your custom color presets. If you don't have any, see the [section on Base16 below](#base16).

At this point, you can run `rainbowterm set -p PRESET` to switch to a new color preset. Alternatively, just run `rainbowterm` to enter interactive mode:

```
j  next               J  next favorite
k  previous           K  previous favorite
p  pick using fzf     f  toggle favorite
l  switch light/dark  s  shuffle
q  quit               i  show info
```

Use <kbd>j</kbd> and <kbd>k</kbd> to navigate through the color presets and instantly apply them. If you have [fzf][fzf], use <kbd>p</kbd> to fuzzy-search for presets by name.

## More features

Rainbowterm lets you keep track of your "favourite" presets. You can view them with `rainbowterm list -f`, edit them with `rainbowterm edit -f`, or choose them interactively by pressive <kbd>f</kbd> in interactive mode. Once you've chosen some favorites, use `rainbowterm set -r` to switch to a random one.

Use `rainbowterm set -s` to select a "smart" favorite. This is determined by three factors with configurable weights: the position of the sun, the brightness of your display, and a random factor. The first time you run it, there will be a popup window asking if [LocateMe][lm] can use Location Services. This lets Rainbowterm determine the solar altitude angle for your current location. If you don't want this behavior, configure `sun_weight` to be zero.

You can also animate the transition between themes. Just pass the `-a` flag to `rainbowterm set`, and it will linearly interpolate between the colors of the current preset and the target. It seems to work better when iTerm2's Metal renderer is enabled.

Finally, you might want to experiment with changing your color preset automatically! Since I always work inside tmux in a single iTerm2 window, I decibed to write a cron job to periodically open a small pane that animates the transition to a random preset: [autorainbow.sh][ar].

## How it works

Rainbowterm works thanks to iTerm2's [proprietary escape codes][esc], which allow you to select a preset or change individual palette colors with escape codes. Rainbowterm also takes special care to make this work inside tmux as well by wrapping the message using tmux escape codes.

## Base16

Rainbowterm works great in conjunction with [Base16][b16]. In particular, you can download ~100 great iTerm2 color presets from [base16-iterm2][b16i2]. If you stick with the ANSI color palette (rather than using the 256 color version), Rainbowterm's updates can instantly affect all your running programs (e.g., shell, tmux, vim). See [chriskempson/base16#174](https://github.com/chriskempson/base16/issues/174) for more explanation.

## Configuration

Here is an example of a complete configuration file, found in `~/.config/rainbowterm/config.ini`. You can edit yours with `rainbowterm edit`.

```ini
# Config for 'rainbowterm load' without '--file'
[iterm2]
# Path to the folder containing com.googlecode.iterm2.plist. This refers to the
# XML file in the folder used in "Load preferences from a custom folder or URL",
# not the binary plist in ~/Library/Preferences.
prefs = /path/to/your/iterm2/prefs

# Config for 'rainbowterm set -a ...'
[animation]
frames = 100  # use 100 interpolated steps
sleep = 50.0  # sleep 50ms between each step
# Reset the theme again 500ms after the end of the animation. Sometimes iTerm2
# and/or tmux don't seem to catch all the escape codes, so this helps ensure
# that we don't get left in a transitional color scheme.
reset_delay = 500.0

# Config for 'rainbowterm set -s'
[smart]
# Weights for the three components:
sun_weight = 10.0     # prefer light/dark themes during the day/night
display_weight = 2.0  # prefer low/high contrast when display is bright/dim
random_weight = 1.0   # uniform random component
# Sun parameters:
sun_bimodal = true
sun_offset = 0.0
sun_min = 0.0
sun_max = 1.0
# Display parameters:
display_number = 0    # which display to consider (see 'brightness -l')
display_offset = 0.0
display_min = 0.2
display_max = 0.5
# Avoid repeating the past 2 smart choices:
avoid_repeat = 2
```

_TODO: Document the rest of the sun/display parameters._

## Dependencies

These dependencies are automatically installed by Homebrew:

- Python 3
- [Astral][as], a Python library used to calculate sunrise and sunset.
- [LocateMe][lm], a tool for accessing your location.
- [brightness][br], a tool for accessing the display brightness.

The following dependencies are optional:

- [fzf][fzf], a fuzzy search tool used in interactive mode.

## License

© 2019 Mitchell Kember

Rainbowterm is available under the MIT License; see [LICENSE](LICENSE.md) for details.

[ar]: https://github.com/mk12/scripts/blob/master/autorainbow.sh
[as]: https://github.com/sffjunkie/astral
[b16]: http://chriskempson.com/projects/base16
[b16i2]: https://github.com/martinlindhe/base16-iterm2
[br]: https://github.com/nriley/brightness
[esc]: https://www.iterm2.com/documentation-escape-codes.html
[fzf]: https://github.com/junegunn/fzf
[hb]: https://brew.sh
[i2]: https://iterm2.com
[lm]: https://iharder.sourceforge.io/current/macosx/locateme
