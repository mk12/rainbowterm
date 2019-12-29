"""This module provides domain objects for colors."""

from typing import Dict, Iterator, Tuple

from rainbowterm.calc import clamp, interpolate, map_number


class LinearColor:
    """A linear RGB color with floating-point channels."""

    def __init__(self, r: float, g: float, b: float):
        """Create a LinearColor from RGB components."""
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1
        self.r = r
        self.g = g
        self.b = b

    def relative_luminance(self) -> float:
        """Calculate the color's relative luminance.

        Spec: https://www.w3.org/TR/WCAG20/#relativeluminancedef.
        """
        return 0.2126 * self.r + 0.7152 * self.g + 0.0722 * self.b

    def interpolate(self, other: "LinearColor", t: float) -> "LinearColor":
        """Linearly interpolates between two colors."""
        return LinearColor(
            interpolate(self.r, other.r, t),
            interpolate(self.g, other.g, t),
            interpolate(self.b, other.b, t),
        )


class BitColor:
    """An sRGB color with 8-bit integer channels."""

    def __init__(self, r: int, g: int, b: int):
        """Create a BitColor from RGB components."""
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255
        self.r = r
        self.g = g
        self.b = b

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BitColor):
            raise NotImplementedError
        return (self.r, self.g, self.b) == (other.r, other.g, other.b)

    def __str__(self) -> str:
        return f"BitColor({self.r}, {self.g}, {self.b})"

    @staticmethod
    def from_linear(color: LinearColor) -> "BitColor":
        """Convert a LinearColor to a BitColor."""

        def f(x: float) -> int:
            if x <= 0.0031308:
                x *= 12.92
            else:
                x = 1.055 * x ** (1 / 2.4) - 0.055
            return round(map_number(x, (0, 1), (0, 255)))

        return BitColor(f(color.r), f(color.g), f(color.b))

    def to_linear(self) -> LinearColor:
        """Convert this BitColor to a LinearColor."""

        def f(x: int) -> float:
            x = map_number(x, (0, 255), (0, 1))
            if x <= 0.04045:
                x /= 12.92
            else:
                x = ((x + 0.055) / 1.055) ** 2.4
            return clamp(x, (0, 1))

        return LinearColor(f(self.r), f(self.g), f(self.b))


class Colors:
    """A collection of colors identified by string keys."""

    FG = "Foreground Color"
    BG = "Background Color"

    def __init__(self, values: Dict[str, BitColor]):
        """Create a new Colors object."""
        assert Colors.FG in values and Colors.BG in values
        self.values = values

    def __getitem__(self, key: str) -> BitColor:
        """Get a color by key."""
        return self.values[key]

    def __iter__(self) -> Iterator[Tuple[str, BitColor]]:
        """Return an iterator over the keys and colors."""
        return iter(self.values.items())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Colors):
            raise NotImplementedError
        return self.values == other.values

    def relative_luminance(self) -> float:
        """Return the relative luminance of the background color."""
        return self.values[Colors.BG].to_linear().relative_luminance()

    def contrast_ratio(self) -> float:
        """Calculate the foreground/background contrast ratio.

        Spec: https://www.w3.org/TR/WCAG20/#contrast-ratiodef.
        """
        r1 = self.values[Colors.FG].to_linear().relative_luminance()
        r2 = self.values[Colors.BG].to_linear().relative_luminance()
        lighter, darker = max(r1, r2), min(r1, r2)
        ratio = ((lighter + 0.05) / (darker + 0.05) - 1) / 20
        return clamp(ratio, (0, 1))

    def interpolate(self, other: "Colors", t: float) -> "Colors":
        """Linearly interpolates between two groups of colors.

        The result only includes colors that are present in both.
        """
        values = {}
        for name in set(self.values) & set(other.values):
            c1 = self.values[name].to_linear()
            c2 = other.values[name].to_linear()
            values[name] = BitColor.from_linear(c1.interpolate(c2, t))
        return Colors(values)
