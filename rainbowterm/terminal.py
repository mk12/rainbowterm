"""This module handles interaction with iTerm2."""

import asyncio
import enum
from typing import AsyncIterator, List, Optional

import iterm2

from rainbowterm.colors import BitColor, Colors
from rainbowterm.presets import Preset


def from_iterm2_color(color: iterm2.Color) -> BitColor:
    """Convert an iterm2.Color to a rainbowterm.colors.Color."""
    # The iterm2.Color fields seem to be fractional, even though the type
    # annotations say int. So we round them.
    return BitColor(round(color.red), round(color.green), round(color.blue))


def to_iterm2_color(color: BitColor) -> iterm2.Color:
    """Convert a rainbowterm.colors.Color to an iterm2.Color."""
    return iterm2.Color(color.r, color.g, color.b)


def from_iterm2_preset(
    name: str, preset: iterm2.ColorPreset
) -> Optional[Preset]:
    """Convert an iterm2.ColorPreset to a rainbowterm.presets.Preset.

    If the preset is missing required colors or has a colors with a non-sRGB
    color space, returns None.
    """
    values = {}
    for c in preset.values:
        if c.alpha != 255:
            return None
        if c.color_space != iterm2.ColorSpace.SRGB:
            return None
        values[c.key] = from_iterm2_color(c)
    if Colors.FG not in values:
        return None
    if Colors.BG not in values:
        return None
    return Preset(name, Colors(values))


class ProfileRef:
    """A reference to an iTerm2 profile."""

    class Kind(enum.Enum):
        """Tag for the kind of profile."""

        NAMED = enum.auto()
        ACTIVE = enum.auto()
        SESSION = enum.auto()

    def __init__(self, kind: Kind, name: Optional[str] = None):
        """Create a new profile reference."""
        self.kind = kind
        self.name = name

    @staticmethod
    def named(name: str) -> "ProfileRef":
        """Reference a profile by name."""
        return ProfileRef(ProfileRef.Kind.NAMED, name)

    @staticmethod
    def active() -> "ProfileRef":
        """Reference the profile used in the current session."""
        return ProfileRef(ProfileRef.Kind.ACTIVE)

    @staticmethod
    def session() -> "ProfileRef":
        """Reference the current session's ephemeral profile."""
        return ProfileRef(ProfileRef.Kind.SESSION)


class Terminal:
    """An abstraction for interacting with iTerm2."""

    def __init__(self, connection: iterm2.Connection):
        """Create a new Terminal connection."""
        self.connection = connection

    @staticmethod
    def run(async_fn, *args):
        """Run an async function that takes a Terminal parameter."""

        async def run(connection: iterm2.Connection):
            await async_fn(*args, Terminal(connection))

        iterm2.run_until_complete(run)

    async def all_preset_names(self) -> List[str]:
        """Return names of all available presets."""
        return await iterm2.ColorPreset.async_get_list(self.connection)

    async def all_presets(self) -> AsyncIterator[Preset]:
        """Return an iterator over all available presets."""

        async def get(name: str) -> Optional[Preset]:
            preset = await iterm2.ColorPreset.async_get(self.connection, name)
            return from_iterm2_preset(name, preset)

        all_presets = await self.all_preset_names()
        for future in asyncio.as_completed(map(get, all_presets)):
            preset = await future
            if preset:
                yield preset

    async def get_profile(self, ref: ProfileRef) -> Optional[iterm2.Profile]:
        """Return the corresponding iterm2.Profile, if it exists."""
        if ref.kind is ref.Kind.NAMED:
            target_name = ref.name
        else:
            app = await iterm2.async_get_app(self.connection)
            session = app.current_window.current_tab.current_session
            profile = await session.async_get_profile()
            if ref.kind is ProfileRef.Kind.SESSION:
                self._profile = profile
                return profile
            assert ref.kind is ProfileRef.Kind.ACTIVE
            target_name = profile.name

        for partial in await iterm2.PartialProfile.async_query(self.connection):
            if partial.name == target_name:
                return await partial.async_get_full_profile()
        return None

    async def active_preset(self, profile: iterm2.Profile) -> Optional[Preset]:
        """Return the profile's active color preset, if it can be determined."""
        async for preset in self.all_presets():
            for key, color in preset.colors:
                iterm2_color = profile.get_color_with_key(key)
                if from_iterm2_color(iterm2_color) != color:
                    break
            else:
                return preset
        return None

    async def set_preset(self, profile: iterm2.Profile, preset_name: str):
        """Set the profile's color preset.

        This should be preferred over set_colors when the preset name is known.
        """
        await profile.async_set_color_preset(
            await iterm2.ColorPreset.async_get(self.connection, preset_name)
        )

    async def set_colors(self, profile: iterm2.Profile, colors: Colors):
        """Set the profile's colors directly."""
        tasks = [
            profile._async_color_set(key, to_iterm2_color(color))
            for key, color in colors
        ]
        await asyncio.gather(*tasks)
