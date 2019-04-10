class Rainbowterm < Formula
  include Language::Python::Virtualenv

  desc "Tool for managing color schemes in iTerm2"
  homepage "https://github.com/mk12/rainbowterm"
  url "https://github.com/mk12/rainbowterm/archive/0.2.0.tar.gz"
  sha256 "48e50d1ff15540df3d143e7fce99bcf541880dac1105ce3d064c20f5d66b002e"
  head "https://github.com/mk12/rainbowterm.git"

  depends_on "python"
  depends_on "brightness" => :recommended
  depends_on "locateme" => :recommended
  depends_on "fzf" => :optional

  resource "astral" do
    url "https://files.pythonhosted.org/packages/86/05/25c772065bb6384789ca0f6ecc9d0bdd0bc210064e5c78453ee15124082e/astral-1.10.1.tar.gz"
    sha256 "d2a67243c4503131c856cafb1b1276de52a86e5b8a1d507b7e08bee51cb67bf1"
  end

  resource "dateutil" do
    url "https://files.pythonhosted.org/packages/ad/99/5b2e99737edeb28c71bcbec5b5dda19d0d9ef3ca3e92e3e925e7c0bb364c/python-dateutil-2.8.0.tar.gz"
    sha256 "c89805f6f4d64db21ed966fda138f8a5ed7a4fdbc1a8ee329ce1b74e3c74da9e"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/rainbowterm", "-h"
  end
end
