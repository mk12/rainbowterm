"""This module provides various calculations."""

from datetime import datetime
from typing import Any, Callable, Dict, Optional, Sequence, Tuple, TypeVar

from astral import Astral


Range = Tuple[float, float]

T = TypeVar("T")


def clamp(x: float, target: Range) -> float:
    """Clamp a value to the given range."""
    lower, upper = target
    return max(lower, min(upper, x))


def map_number(x: float, source: Range, target: Range) -> float:
    """Re-maps a number from one range to another, and clamps it."""
    a, b = source
    c, d = target
    result = (x - a) / (b - a) * (d - c) + c
    return clamp(result, target)


def interpolate(x1: float, x2: float, t: float) -> float:
    """Linearly interpolate between two numbers."""
    x1 = float(x1)
    x2 = float(x2)
    return x1 + t * (x2 - x1)


def closeness(x: float, y: float) -> float:
    """Calculate a statistic representing how close x and y are.

    Assumes x and y are between 0 and 1. The result is 1 if x and y are the
    same, 0 if they are as far apart as possible, and in between otherwise.
    """
    return clamp(1 - (x - y) ** 2, (0, 1))


def normalized_solar_elevation(
    latitude: float, longitude: float, date_time: datetime
) -> float:
    """Return the solar elevation as a number from 0 to 1.

    If date_time is naive, it is assumed to be in UTC. The result is 0 for the
    lowest solar elevation (solar midnight), 0.5 for sunset/sunrise, and 1 for
    the highest solar elevation (solar noon).
    """
    astral = Astral()
    elevation = lambda t: astral.solar_elevation(t, latitude, longitude)
    highest = elevation(astral.solar_noon_utc(date_time.date(), longitude))
    lowest = elevation(astral.solar_midnight_utc(date_time.date(), longitude))
    actual = elevation(date_time)
    if actual > 0:
        return map_number(actual, (0, highest), (0.5, 1))
    return map_number(actual, (lowest, 0), (0, 0.5))


def normalized_ranks(
    values: Sequence[T],
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> Dict[T, float]:
    """Calculate the normalized ranks for a set of values."""
    if not values:
        return {}
    if len(values) == 1:
        return {values[0]: 0.5}
    values = sorted(values, key=key, reverse=reverse)
    n = len(values) - 1
    return {x: i / n for i, x in enumerate(values)}


def bimodal_normalized_ranks(
    values: Sequence[T],
    middle: Any,
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> Dict[T, float]:
    """Like normalized_ranks, but assumes a bimodal distribution.

    The result has all values below middle assigned ranks from 0 to 0.5, and all
    values above middle assigned ranks from 0.5 to 1.
    """
    if not key:
        key = lambda x: x
    left = [x for x in values if key(x) <= middle]
    right = [x for x in values if key(x) > middle]
    if reverse:
        left, right = right, left
    # Take the average of gaps between ranks from both sides and use that in the
    # middle, so that we don't have both left and right touching at 0.5.
    left_gap = 0.5 / (len(left) - 1) if len(left) > 1 else 0
    right_gap = 0.5 / (len(right) - 1) if len(right) > 1 else 0
    average_gap = (left_gap + right_gap) / 2
    half_gap = average_gap / 2
    left_ranks = {
        x: map_number(rank, (0, 1), (0, 0.5 - half_gap))
        for x, rank in normalized_ranks(left, key=key, reverse=reverse).items()
    }
    right_ranks = {
        x: map_number(rank, (0, 1), (0.5 + half_gap, 1))
        for x, rank in normalized_ranks(right, key=key, reverse=reverse).items()
    }
    return {**left_ranks, **right_ranks}
