from typing import Any, Dict

import iterm2

import pytest

import rainbowterm.colors as c
import rainbowterm.terminal as t

from helpers import stub  # noqa


def make_colors(fg: c.BitColor, bg: c.BitColor) -> c.Colors:
    return c.Colors({c.Colors.FG: fg, c.Colors.BG: bg})


def stub_preset(fg: Dict[str, Any], bg: Dict[str, Any]) -> Any:
    args = dict(a=255, color_space=iterm2.ColorSpace.SRGB)
    return stub(
        values=[
            iterm2.ColorPreset.Color(**{**args, "key": c.Colors.FG, **fg}),
            iterm2.ColorPreset.Color(**{**args, "key": c.Colors.BG, **bg}),
        ]
    )


def test_from_iterm2_color():
    assert t.from_iterm2_color(iterm2.Color(1, 2, 3)) == c.BitColor(1, 2, 3)


def test_to_iterm2_color():
    color = c.BitColor(1, 2, 3)
    iterm2_color = iterm2.Color(1, 2, 3)
    # iTerm2.Color does not implement __eq__.
    assert repr(t.to_iterm2_color(color)) == repr(iterm2_color)


def test_from_iterm2_preset():
    preset = stub_preset(fg=dict(r=1, g=2, b=3), bg=dict(r=7, g=8, b=9))
    colors = make_colors(fg=c.BitColor(1, 2, 3), bg=c.BitColor(7, 8, 9))
    assert t.from_iterm2_preset(preset) == colors


def test_from_iterm2_preset_missing_color():
    preset = stub_preset(fg=dict(r=1, g=2, b=3), bg=dict(r=7, g=8, b=9))
    preset.values.pop()
    assert t.from_iterm2_preset(preset) is None


def test_from_iterm2_preset_invalid_alpha():
    preset = stub_preset(fg=dict(r=1, g=2, b=3, a=254), bg=dict(r=7, g=8, b=9))
    assert t.from_iterm2_preset(preset) is None


def test_from_iterm2_preset_invalid_color_space():
    preset = stub_preset(
        fg=dict(r=1, g=2, b=3, color_space="device"), bg=dict(r=7, g=8, b=9)
    )
    assert t.from_iterm2_preset(preset) is None


@pytest.mark.asyncio
async def test_terminal_all_presets(monkeypatch):
    async def async_get_list(self):
        return ["foo"]

    async def async_get(self, name):
        assert name == "foo"
        return stub_preset(fg=dict(r=1, g=2, b=3), bg=dict(r=7, g=8, b=9))

    monkeypatch.setattr(iterm2.ColorPreset, "async_get_list", async_get_list)
    monkeypatch.setattr(iterm2.ColorPreset, "async_get", async_get)
    presets = [p async for p in t.Terminal(None).all_presets()]
    assert presets == [
        ("foo", make_colors(fg=c.BitColor(1, 2, 3), bg=c.BitColor(7, 8, 9)))
    ]


@pytest.mark.asyncio
async def test_terminal_get_profile(monkeypatch):
    async def async_get_app(connection):
        async def async_get_profile():
            return "foo"

        return stub(
            current_window=stub(
                current_tab=stub(
                    current_session=stub(async_get_profile=async_get_profile)
                )
            )
        )

    monkeypatch.setattr(iterm2, "async_get_app", async_get_app)
    profile = await t.Terminal(None).get_profile(t.Profile.session())
    assert profile == "foo"
