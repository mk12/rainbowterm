class Rainbowterm < Formula
  desc "Color theme manager for iTerm2"
  homepage "https://github.com/mk12/rainbowterm"
  url "https://github.com/mk12/rainbowterm/archive/0.1.0.tar.gz"
  sha256 "bf11151dc2606a49dfa97117b45ef1b575a03c111f9c15a6c5a79b3229b48959"
  head "https://github.com/mk12/rainbowterm.git"

  depends_on "python"

  def install
    cp "rainbowterm.py", "rainbowterm"
    bin.install "rainbowterm"
  end

  test do
    system "#{bin}/rainbowterm", "-h"
  end
end
