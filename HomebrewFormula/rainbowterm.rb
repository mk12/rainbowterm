class Rainbowterm < Formula
  desc "Color theme manager for iTerm2"
  homepage "https://github.com/mk12/rainbowterm"
  url "https://github.com/mk12/rainbowterm/archive/0.1.0.tar.gz"
  head "https://github.com/mk12/rainbowterm.git"

  depends_on "python"

  def install
    system "cp", "rainbowterm.py", "rainbowterm"
    bin.install "rainbowterm"
  end

  test do
    system "#{bin}/rainbowterm", "-h"
  end
end
