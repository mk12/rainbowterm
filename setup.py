from setuptools import setup

setup(
    name="rainbowterm",
    version="0.4.0",
    description="Tool for managing color themes in iTerm2",
    packages=["rainbowterm"],
    package_data={"rainbowterm": ["default_config.ini"]},
    entry_points={"console_scripts": ["rainbowterm = rainbowterm.main:main"]},
    install_requires=["astral", "iterm2", "python-dateutil"],
    url="https://github.com/mk12/rainbowterm",
)
