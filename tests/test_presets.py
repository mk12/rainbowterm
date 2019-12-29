from math import isclose

import rainbowterm.colors as c
import rainbowterm.presets as p


def make_preset(name: str = "Test") -> p.Preset:
    return p.Preset(
        name=name,
        colors=c.Colors(
            values={
                c.Colors.FG: c.BitColor(0, 0, 0),
                c.Colors.BG: c.BitColor(255, 255, 255),
                "Error": c.BitColor(255, 0, 0),
            }
        )
    )


def test_preset_brightness():
    assert isclose(1.0, make_preset().brightness())


def test_preset_contrast():
    assert isclose(1.0, make_preset().contrast())


def test_smart_score_total():
    score = p.SmartScore(sun=1, display=2, random=3)
    assert score.total() == 6


def test_preset_selector_light_dark_alternate():
    pass


def test_preset_selector_smart_scores():
    pass


def test_preset_selector_smart_choice():
    pass


def test_preset_selector_animation_frames():
    pass
