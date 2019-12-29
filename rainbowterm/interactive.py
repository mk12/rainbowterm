# Menu shown in interactive mode.
INTERACTIVE_MENU = """\
j  next               J  next favorite
k  previous           K  previous favorite
p  pick using fzf     f  toggle favorite
l  switch light/dark  s  shuffle
q  quit               i  show info
"""

def set_iterm_colors(key, value):
    """Print an iTerm2 escape code to update color settings."""
    msg = f"\x1B]1337;SetColors={key}={value}\x07"
    if "TMUX" in os.environ:
        msg = f"\x1BPtmux;\x1B{msg}\x1B\\"
    print(msg, end="", flush=True)


def read_char() -> str:
    """Read a single character from stdin (without pressing enter)."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


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
        elif char == "i":
            brightness = rainbow.presets[self.current]["brightness"]
            contrast = rainbow.presets[self.current]["contrast"]
            self.info(f"brightness={brightness:.3f}, contrast={contrast:.3f}")
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
