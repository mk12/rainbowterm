# Rainbowterm

Rainbowterm is a tool for managing color schemes in [iTerm2][i2].

Why use Rainbowterm?

- You like changing your color scheme often.
- You want it to be as easy as possible.

Here are its coolest features:

- Switch to a new color scheme with [fzf][fzf].
- Animate the transition between themes with linear interpolation.
- (**Coming soon**) Automatically choose themes based on time of day and ambient light.

## Install

Install with [Homebrew][hb]:

1. `brew tap mk12/rainbowterm https://github.com/mk12/rainbowterm`
2. `brew install rainbowterm`

## Usage

Run `rainbowterm -h` to see the available commands:

- `rainbowterm` with no arguments enters interactive mode.
- `rainbowterm set` allows you to switch to a new color preset.
- `rainbowterm edit` edits your config file (favorites file with `-f`).
- `rainbowterm list` lists all your color presets (favorites only with `-f`).
- `rainbowterm load` loads color presets from iTerm2 preferences.

For more information on a particular command `CMD`, run `rainbowterm CMD -h`.

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
j  next
k  previous
s  shuffle
p  pick using fzf
l  switch light/dark
f  toggle favorite
q  quit
```

Use <kbd>j</kbd> and <kbd>k</kbd> to navigate through the color presets and instantly apply them. If you have [fzf][fzf], use <kbd>p</kbd> to fuzzy-search for presets by name.

## More features

Rainbowterm lets you keep track of your "favourite" presets. You can view them with `rainbowterm list -f`, edit them with `rainbowterm edit -f`, or choose them interactively by pressive <kbd>f</kbd> in interactive mode. Once you've chosen some favorites, you can run `rainbowterm set -r` to pick a random one, or (**coming soon**) `rainbowterm set -s` to pick a smart-random favorite based on the time of day and the MacBook ambient light sensor.

You can also animate the transition between themes. Just pass the `-a` flag to `rainbowterm set`, and it will linearly interpolate between the colors of the current preset and the target. It seems to work better when iTerm2's Metal renderer is enabled. You can configure the animation with the following two options in `config.ini`:

```ini
[animation]
frames = 100  # use 100 interpolated steps
sleep = 50    # sleep 50ms between each step
```

Finally, you might want to experiment with changing your color preset automatically! Since I always work inside tmux in a single iTerm2 window, I decibed to write a cron job to periodically open a small pane that animates the transition to a random preset: [autorainbow.sh][ar].

## How it works

Rainbowterm works thanks to iTerm2's [proprietary escape codes][esc], which allow you to select a preset or change individual palette colors with escape codes. Rainbowterm also takes special care to make this work inside tmux as well by wrapping the message using tmux escape codes.

## Base16

Rainbowterm works great in conjunction with [Base16][b16]. In particular, you can download ~100 great iTerm2 color presets from [base16-iterm2][b16i2]. If you stick with the ANSI color palette (rather than using the 256 color version), Rainbowterm's updates can instantly affect all your running programs (e.g., shell, tmux, vim). See [chriskempson/base16#174](https://github.com/chriskempson/base16/issues/174) for more explanation.

## License

© 2019 Mitchell Kember

Rainbowterm is available under the MIT License; see [LICENSE](LICENSE.md) for details.

[i2]: https://iterm2.com
[esc]: https://www.iterm2.com/documentation-escape-codes.html
[hb]: https://brew.sh
[fzf]: https://github.com/junegunn/fzf
[b16]: http://chriskempson.com/projects/base16
[b16i2]: https://github.com/martinlindhe/base16-iterm2
[ar]: https://github.com/mk12/scripts/blob/master/autorainbow.sh
