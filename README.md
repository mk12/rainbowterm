# Rainbowterm

Rainbowterm is a tool for managing color schemes in [iTerm2][i2].

Why use Rainbowterm?

- You like changing your color scheme often.
- You want it to be as easy as possible.

## Install

Install with [Homebrew][hb]:

    brew tap mk12/rainbowterm https://github.com/mk12/rainbowterm
    brew install mk12/rainbowterm/rainbowterm

## Getting started

First, make sure you enable "Load preferences from a custom folder or URL" in your iTerm2 preferences. iTerm2 will save `com.googlecode.iterm2.plist` in the folder you pick. (If you have a dotfiles repository, I recommend storing it there.)

Next, run `rainbowterm edit` to edit `~/.config/rainbowterm/config.ini`, and enter the path you just chose:

```
[iterm2]
plist = /path/to/your/com.googlecode.iterm2.plist
# For example, mine is ~/GitHub/dotfiles/iterm2/com.googlecode.iterm2.plist
```

Now, run `rainbowterm load`. This will parse all your custom color presets. If you don't have any, see the section on Base16 below.

At this point, you can run `rainbowterm` to enter interactive mode:

```
j  next
k  previous
s  shuffle
p  pick using fzf
l  switch light/dark
f  toggle favorite
q  quit
```

Use `j` and `k` to navigate through the color presets and instantly apply them. This is possible thanks to iTerm2's [proprietary escape codes][esc]. If you have [fzf][fzf] installed, use `p` to fuzzy-search for presets by name.

You can also mark presets as "favorite" using `f`. This just writes to `~/.config/rainbowterm/favorites`, which you can view quickly with `rainbowterm edit -f`. The favorites are used when you pick a random preset with `rainbowterm set -r` or `rainbowterm set -s`.

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

TODO

## Automatic

TODO

## License

© 2019 Mitchell Kember

Rainbowterm is available under the MIT License; see [LICENSE](LICENSE.md) for details.

[i2]: https://iterm2.com
[esc]: https://www.iterm2.com/documentation-escape-codes.html
[hb]: https://brew.sh
[fzf]: https://github.com/junegunn/fzf
