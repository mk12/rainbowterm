from math import isclose

import pytest

import rainbowterm.colors as c


BLACK = c.BitColor(0, 0, 0)
WHITE = c.BitColor(255, 255, 255)


def make_colors(fg: c.BitColor, bg: c.BitColor) -> c.Colors:
    return c.Colors({c.Colors.FG: fg, c.Colors.BG: bg})


def test_linear_color_valid():
    c.LinearColor(0, 0.5, 1)


def test_linear_color_invalid():
    with pytest.raises(AssertionError):
        c.LinearColor(-1, 0, 0)
    with pytest.raises(AssertionError):
        c.LinearColor(2, 0, 0)


def test_linear_color_relative_luminance():
    assert isclose(0.0, c.LinearColor(0.0, 0.0, 0.0).relative_luminance())
    assert isclose(0.5, c.LinearColor(0.5, 0.5, 0.5).relative_luminance())
    assert isclose(1.0, c.LinearColor(1.0, 1.0, 1.0).relative_luminance())


def test_linear_color_interpolate():
    c1 = c.LinearColor(0.5, 0, 0.3)
    c2 = c.LinearColor(0.9, 0.1, 0.7)
    interpolated = c1.interpolate(c2, 0.8)
    assert isclose(interpolated.r, 0.82)
    assert isclose(interpolated.g, 0.08)
    assert isclose(interpolated.b, 0.62)


def test_bit_color_valid():
    c.BitColor(0, 128, 255)


def test_bit_color_invalid():
    with pytest.raises(AssertionError):
        c.BitColor(-1, 0, 0)
    with pytest.raises(AssertionError):
        c.BitColor(256, 0, 0)


def test_colors_getitem():
    colors = make_colors(fg=BLACK, bg=WHITE)
    assert colors["Foreground Color"] == BLACK
    assert colors["Background Color"] == WHITE


def test_colors_iter():
    colors = make_colors(fg=BLACK, bg=WHITE)
    assert dict(colors) == {
        "Foreground Color": BLACK,
        "Background Color": WHITE,
    }


def test_colors_relative_luminance():
    assert isclose(1, make_colors(fg=BLACK, bg=WHITE).relative_luminance())
    assert isclose(0, make_colors(fg=WHITE, bg=BLACK).relative_luminance())
    assert isclose(0, make_colors(fg=BLACK, bg=BLACK).relative_luminance())
    assert isclose(1, make_colors(fg=WHITE, bg=WHITE).relative_luminance())


def test_colors_contrast_ratio():
    assert isclose(1, make_colors(fg=BLACK, bg=WHITE).contrast_ratio())
    assert isclose(1, make_colors(fg=WHITE, bg=BLACK).contrast_ratio())
    assert isclose(0, make_colors(fg=BLACK, bg=BLACK).contrast_ratio())
    assert isclose(0, make_colors(fg=WHITE, bg=WHITE).contrast_ratio())


def test_interpolate_colors():
    colors1 = make_colors(fg=BLACK, bg=WHITE)
    colors2 = make_colors(fg=WHITE, bg=BLACK)
    assert colors1.interpolate(colors2, 0)[c.Colors.FG] == BLACK
    assert colors1.interpolate(colors2, 1)[c.Colors.FG] == WHITE
    assert colors1.interpolate(colors2, 0)[c.Colors.BG] == WHITE
    assert colors1.interpolate(colors2, 1)[c.Colors.BG] == BLACK
