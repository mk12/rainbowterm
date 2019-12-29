class Rainbowterm < Formula
  include Language::Python::Virtualenv

  desc "Tool for managing color schemes in iTerm2"
  homepage "https://github.com/mk12/rainbowterm"
  url "https://github.com/mk12/rainbowterm/archive/0.4.0.tar.gz"
  sha256 "7c960d5532f5e5d3200c0e428203eafba275d1d63110de96253303a53f8e4b52"
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

  resource "iterm2" do
    url "https://files.pythonhosted.org/packages/11/f1/c69ff765fb32499d3890cd74e2001bb6e6b72d8807013a5ea1cd61add22a/iterm2-1.8.tar.gz"
    sha256 "7ddfe222ee84acd49fa370f2cc42e8f7882ad9573194ed394ac92413e3b52367"
  end

  resource "protobuf" do
    url "https://files.pythonhosted.org/packages/12/b9/e7c6a58613c9fe724d1ff9f2353fa48901e6b1b99d0ba64c36a8de2cfa45/protobuf-3.10.0.tar.gz"
    sha256 "db83b5c12c0cd30150bb568e6feb2435c49ce4e68fe2d7b903113f0e221e58fe"
  end

  resource "pytz" do
    url "https://files.pythonhosted.org/packages/af/be/6c59e30e208a5f28da85751b93ec7b97e4612268bb054d0dff396e758a90/pytz-2018.9.tar.gz"
    sha256 "d5f05e487007e29e03409f9398d074e158d920d36eb82eaf66fb1136b0c5374c"
  end

  resource "six" do
    url "https://files.pythonhosted.org/packages/dd/bf/4138e7bfb757de47d1f4b6994648ec67a51efe58fa907c1e11e350cddfca/six-1.12.0.tar.gz"
    sha256 "d16a0141ec1a18405cd4ce8b4613101da75da0e9a7aec5bdd4fa804d0e0eba73"
  end

  resource "websockets" do
    url "https://files.pythonhosted.org/packages/e9/2b/cf738670bb96eb25cb2caf5294e38a9dc3891a6bcd8e3a51770dbc517c65/websockets-8.1.tar.gz"
    sha256 "5c65d2da8c6bce0fca2528f69f44b2f977e06954c8512a952222cea50dad430f"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/rainbowterm", "-h"
  end
end
