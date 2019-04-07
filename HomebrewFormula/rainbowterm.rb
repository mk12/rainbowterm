class Rainbowterm < Formula
  desc "Color scheme manager for iTerm2"
  homepage "https://github.com/mk12/rainbowterm"
  url "https://github.com/mk12/rainbowterm/archive/0.2.0.tar.gz"
  sha256 "48e50d1ff15540df3d143e7fce99bcf541880dac1105ce3d064c20f5d66b002e"
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
