from datetime import datetime
from math import isclose

import rainbowterm.calc as c


def test_clamp():
    assert c.clamp(0, (0, 0)) == 0
    assert c.clamp(0, (0, 1)) == 0
    assert c.clamp(0, (1, 1)) == 1
    assert c.clamp(0, (1, 2)) == 1
    assert c.clamp(3, (1, 2)) == 2
    assert c.clamp(1, (0, 2)) == 1


def test_map_number():
    assert c.map_number(0, [0, 1], [0, 1]) == 0
    assert c.map_number(0, [0, 1], [0, 10]) == 0
    assert c.map_number(1, [0, 1], [0, 10]) == 10
    assert c.map_number(1, [0, 2], [0, 10]) == 5


def test_interpolate():
    assert c.interpolate(0, 1, 0) == 0
    assert c.interpolate(0, 1, 1) == 1
    assert c.interpolate(0, 2, 0.5) == 1
    assert c.interpolate(0, 1, 2) == 2
    assert c.interpolate(0, 1, -1) == -1


def test_closeness():
    assert c.closeness(0, 0) == 1
    assert c.closeness(0, 1) == 0
    assert c.closeness(0.5, 0.5) == 1
    assert c.closeness(0.4, 0.6) > c.closeness(0.3, 0.7)


def test_normalized_solar_elevation():
    tolerance = {"rel_tol": 0.1, "abs_tol": 0.05}
    assert isclose(
        c.normalized_solar_elevation(0, 0, datetime(2000, 1, 1, 0)),
        0,
        **tolerance,
    )
    assert isclose(
        c.normalized_solar_elevation(0, 0, datetime(2000, 1, 1, 6)),
        0.5,
        **tolerance,
    )
    assert isclose(
        c.normalized_solar_elevation(0, 0, datetime(2000, 1, 1, 12)),
        1,
        **tolerance,
    )


def test_normalized_ranks():
    assert c.normalized_ranks([]) == {}
    assert c.normalized_ranks([0]) == {0: 0.5}
    assert c.normalized_ranks([0, 1]) == {0: 0, 1: 1}
    assert c.normalized_ranks([0, 99, 4]) == {0: 0, 4: 0.5, 99: 1}
    assert c.normalized_ranks([70, 5, 1, 7, 32]) == {
        1: 0,
        5: 0.25,
        7: 0.5,
        32: 0.75,
        70: 1,
    }
    assert c.normalized_ranks([-10, 1], key=abs) == {1: 0, -10: 1}
    assert c.normalized_ranks([5, 1, 2], key=None, reverse=True) == {
        5: 0,
        2: 0.5,
        1: 1,
    }


def test_bimodal_normalized_ranks():
    assert c.bimodal_normalized_ranks([0], 0) == {0: 0.25}
    assert c.bimodal_normalized_ranks([0], -1) == {0: 0.75}
    assert c.bimodal_normalized_ranks([0, 1], 0) == {0: 0.25, 1: 0.75}
    assert c.bimodal_normalized_ranks([0, 1], 1) == {0: 0, 1: 0.375}
    assert c.bimodal_normalized_ranks([0, 1], 1) == {0: 0, 1: 0.375}
    assert c.bimodal_normalized_ranks(
        ["1", "99", "19", "90", "95", "3"], 50, key=int, reverse=True
    ) == {"99": 0, "95": 0.1875, "90": 0.375, "19": 0.625, "3": 0.8125, "1": 1}
