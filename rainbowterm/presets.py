"""This module provides color preset objects and selection routines."""

import random
from datetime import datetime
from typing import Dict, Iterable, Iterator, List, NamedTuple, Optional

from rainbowterm.calc import (
    bimodal_normalized_ranks,
    clamp,
    closeness,
    map_number,
    normalized_ranks,
    normalized_solar_elevation,
)
from rainbowterm.colors import Colors
from rainbowterm.files import Config, FileStore, MAX_SMART_HISTORY
from rainbowterm.services import display_brightness, geolocation
from rainbowterm.utils import FatalError


class Preset(NamedTuple):
    """A color preset, comprising a name and set of colors."""

    name: str
    colors: Colors

    def brightness(self) -> float:
        """Return the brightness of the preset."""
        return self.colors.relative_luminance()

    def contrast(self) -> float:
        """Return the contrast of the preset."""
        return self.colors.contrast_ratio()


class SmartScore(NamedTuple):
    """A score used for ranking presets.

    The score includes 3 pre-weighted terms. Higher numbers are better.
    """

    sun: float
    display: float
    random: float

    def total(self) -> float:
        """Return the total score as a single number."""
        return self.sun + self.display + self.random


class PresetSelector:
    """Class that manages color presets and selects from among them."""

    def __init__(
        self, presets: Iterable[Preset], config: Config, filestore: FileStore
    ):
        """Create a new PresetSelector."""
        self.presets = {p.name: p for p in presets}
        self.config = config
        self.filestore = filestore

    def light_dark_alternate(self, preset_name: str) -> Optional[str]:
        """Return the corresponding light/dark preset name, or None."""
        assert preset_name in self.presets
        for a, b in [("light", "dark"), ("dark", "light")]:
            for c in [a, "-" + a]:
                for d in [b, "-" + b]:
                    for replacement in [(c, ""), (c, d)]:
                        other = preset_name.replace(*replacement)
                        if other != preset_name and other in self.presets:
                            return other
        return None

    def smart_scores(
        self, presets: List[Preset], score_time: datetime
    ) -> Dict[Preset, SmartScore]:
        """Calculate components of scores for smart_choice."""
        # Get the weight for each part of the score.
        parts = "sun", "display", "random"
        weights = {p: self.config.float("smart", f"{p}_weight") for p in parts}

        # Rank presets from 0 to 1 on brightness and contrast values. We leave
        # sun_ranks sorted so that high sun altitude is related to high preset
        # brightness, and reverse display_ranks so that high display brightness
        # is related to low preset contrast.
        if self.config.bool("smart", "sun_bimodal"):
            sun_ranks = bimodal_normalized_ranks(
                presets, middle=0.5, key=Preset.brightness
            )
        else:
            sun_ranks = normalized_ranks(presets, key=Preset.brightness)
        display_ranks = normalized_ranks(
            presets, key=Preset.contrast, reverse=True
        )

        def calculate_ideal_rank(name, base_value):
            """Calculate the ideal rank (that would get the best score)."""
            offset = self.config.float("smart", f"{name}_offset")
            source_range = (
                self.config.float("smart", f"{name}_min", ge=0, le=1),
                self.config.float("smart", f"{name}_max", ge=0, le=1),
            )
            if base_value is None:
                return None
            return map_number(clamp(base_value + offset), source_range, (0, 1))

        # Calculate the ideal values for sun and display ranks.
        ideal_sun_rank = calculate_ideal_rank(
            "sun", normalized_solar_elevation(*geolocation(), score_time)
        )
        display_num = self.config.int("smart", "display_number", ge=0)
        ideal_display_rank = calculate_ideal_rank(
            "display", display_brightness(display_num)
        )

        def score(preset: Preset) -> SmartScore:
            """Calculate a score for choosing the preset (higher is better)."""
            sun_rank = sun_ranks[preset]
            display_rank = display_ranks[preset]
            terms = {p: 0.0 for p in parts}
            if ideal_sun_rank is not None:
                terms["sun"] = closeness(sun_rank, ideal_sun_rank)
            if ideal_display_rank is not None:
                terms["display"] = closeness(display_rank, ideal_display_rank)
            terms["random"] = random.random()
            score = {p: weights[p] * terms[p] for p in parts}
            return SmartScore(**score)

        return {p: score(p) for p in presets}

    def smart_choice(
        self, score_time: datetime, consider_repetition: bool
    ) -> Preset:
        """Choose a preset with the highest smart score."""
        if not self.presets:
            raise FatalError("no color presets to choose from")
        avoid_repeat = 0
        if consider_repetition:
            avoid_repeat = self.config.int(
                "smart", "avoid_repeat", ge=0, le=MAX_SMART_HISTORY
            )
        # If avoid_repeat is N, do not consider the last N smart choices.
        if avoid_repeat == 0:
            options = list(self.presets)
        else:
            avoid = set(self.filestore.smart_history[-avoid_repeat:])
            options = [p for p in self.presets if p not in avoid]
        if not options:
            raise FatalError(
                f"{avoid_repeat}: cannot satisfy smart.avoid_repeat config"
            )
        # Choose the preset with the highest smart score.
        scores = self.smart_scores(options, score_time)
        choice = max(options, key=lambda p: scores[p].total)
        self.filestore.smart_history += [choice.name]
        return choice

    def animation_frames(
        self, start_preset_name: str, end_preset_name: str
    ) -> Iterator[Colors]:
        """Update the current preset using a fading animation.

        FIXME FIXME FIXME
        """
        frames = self.config.int("animation", "frames", gt=0)
        start_colors = self.presets[start_preset_name].colors
        end_colors = self.presets[end_preset_name].colors
        for i in range(1, frames + 1):
            yield start_colors.interpolate(end_colors, i / frames)
