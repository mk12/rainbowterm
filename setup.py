from setuptools import setup

setup(
    name="rainbowterm",
    version="0.4.0",
    description="Tool for managing color schemes in iTerm2",
    py_modules=["rainbowterm"],
    entry_points={"console_scripts": ["rainbowterm = rainbowterm:main"]},
    depends=["astral", "dateutil"],
    url="https://github.com/mk12/rainbowterm",
)
