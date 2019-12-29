from collections import namedtuple


def stub(**d) -> object:
    """Create an object from a dict."""
    return namedtuple("object", d.keys())(*d.values())
