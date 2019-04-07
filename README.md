# Rainbowterm

Rainbowterm is a tool for managing color schemes in [iTerm2][i2].

Why use Rainbowterm?

- You like changing your color scheme often.
- You want it to be as easy as possible.

Here are its coolest features:

- Switch to a new color theme with [fzf][fzf].
- Animate the transition between themes with linear interpolation.
- (**Coming soon**) Automatically choose themes based on time of day and ambient light.

## Install

Install with [Homebrew][hb]:

1. `brew tap mk12/rainbowterm https://github.com/mk12/rainbowterm`
2. `brew install mk12/rainbowterm/rainbowterm`

## Getting started

First, make sure you enable _Load preferences from a custom folder or URL_ in your iTerm2 preferences. iTerm2 will save `com.googlecode.iterm2.plist` in the folder you pick. (If you have a dotfiles repository, I recommend storing it there.)

Next, run `rainbowterm edit` to edit `~/.config/rainbowterm/config.ini`, and enter the following:

```
[iterm2]
plist = /path/to/your/com.googlecode.iterm2.plist
# For example, mine is ~/GitHub/dotfiles/iterm2/com.googlecode.iterm2.plist
```

Now, run `rainbowterm load` to parse your custom color presets. If you don't have any, see the section on Base16 below.

At this point, you can run `rainbowterm set -p PRESET` to switch to the given color preset. Alternatively, run `rainbowterm` to enter interactive mode:

```
j  next
k  previous
s  shuffle
p  pick using fzf
l  switch light/dark
f  toggle favorite
q  quit
```

Use <kbd>j</kbd> and <kbd>k</kbd> to navigate through the color presets and instantly apply them. This is possible thanks to iTerm2's [proprietary escape codes][esc]. (It also works if you're inside tmux.) If you have [fzf][fzf] installed, use <kbd>p</kbd> to fuzzy-search for presets by name.

You can also choose "favorite" presets using <kbd>f</kbd>. This just writes to `~/.config/rainbowterm/favorites`, which you can view with `rainbowterm edit -f`. The favorites are used for `rainbowterm set -r` (random preset) and `rainbowterm set -s` (smart-random, based on time of day and ambient light).

Last, but not least, you can animate the transition between themes using the `-a` flag with `rainbowterm set`. This seems to work better when the Metal renderer is enabled. You can configure it with the following two options in `config.ini`:

```
[animation]
frames = 100  # use 100 interpolated steps
sleep = 50    # sleep 50ms between each step
```

## Usage

Run `rainbowterm -h` to see the available commands:

- `rainbowterm` with no arguments enters interactive mode.
- `rainbowterm set` allows you to set the color preset.
- `rainbowterm edit` edits your config file (favorites file with `-f`).
- `rainbowterm list` lists all your color presets (favorites only with `-f`).
- `rainbowterm load` loads color presets from iTerm2 preferences.

For more information on a particular command `CMD`, run `rainbowterm CMD -h`.

## Base16

Rainbowterm works great in conjunction with [Base16][b16]. In particular, you can get ~100 great iTerm2 color presets from [base16-iterm2][b16i2]. If you stick with the ANSI color palette (rather than using the 256 color version), Rainbowterm's updates can instantly affect all your running programs (e.g., shell, tmux, vim). See [chriskempson/base16#174](https://github.com/chriskempson/base16/issues/174) for more explanation.

## License

© 2019 Mitchell Kember

Rainbowterm is available under the MIT License; see [LICENSE](LICENSE.md) for details.

[i2]: https://iterm2.com
[esc]: https://www.iterm2.com/documentation-escape-codes.html
[hb]: https://brew.sh
[fzf]: https://github.com/junegunn/fzf
[b16]: http://chriskempson.com/projects/base16
[b16i2]: https://github.com/martinlindhe/base16-iterm2
