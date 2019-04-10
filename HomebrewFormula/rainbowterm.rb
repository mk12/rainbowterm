class Rainbowterm < Formula
  include Language::Python::Virtualenv

  desc "Tool for managing color schemes in iTerm2"
  homepage "https://github.com/mk12/rainbowterm"
  url "https://github.com/mk12/rainbowterm/archive/0.3.0.tar.gz"
  sha256 "4de619c125e5430f367fd63357ffbd91b83f87719e64a80e7a9663ffcbe94584"
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

  resource "pytz" do
    url "https://files.pythonhosted.org/packages/af/be/6c59e30e208a5f28da85751b93ec7b97e4612268bb054d0dff396e758a90/pytz-2018.9.tar.gz"
    sha256 "d5f05e487007e29e03409f9398d074e158d920d36eb82eaf66fb1136b0c5374c"
  end

  resource "six" do
    url "https://files.pythonhosted.org/packages/dd/bf/4138e7bfb757de47d1f4b6994648ec67a51efe58fa907c1e11e350cddfca/six-1.12.0.tar.gz"
    sha256 "d16a0141ec1a18405cd4ce8b4613101da75da0e9a7aec5bdd4fa804d0e0eba73"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/rainbowterm", "-h"
  end
end
