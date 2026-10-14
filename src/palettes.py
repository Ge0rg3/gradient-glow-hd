"""Colour palettes and film grain"""

import colorsys

import numpy as np
from PIL import Image

from config import DITHER_HALFWIDTH, STYLES


def _draw_grain(
    grain: dict, width: int, height: int, rng: np.random.Generator, cell_size: float
) -> np.ndarray:
    """Draw monochrome grain in 8-bit levels"""
    # Size grain grid
    columns, rows = width, height
    if cell_size > 1:
        columns = int(np.ceil(width / cell_size))
        rows = int(np.ceil(height / cell_size))

    # Draw uniform noise with softened limits
    noise = rng.uniform(
        -grain["uniform_halfwidth"], grain["uniform_halfwidth"], (rows, columns)
    )
    noise += rng.normal(0, grain["gauss_sigma"], (rows, columns))

    # Enlarge coarse grain to output size
    if cell_size > 1:
        coarse = Image.fromarray(noise.astype(np.float32))
        noise = np.asarray(coarse.resize((width, height), Image.NEAREST), float)
    return noise


def find_palette(model: dict, name: str) -> dict | None:
    """Return palette by name, None if unknown"""
    # Use original colour
    if name in model["palettes"]:
        return model["palettes"][name]

    # Parse <style>-<hue> shade
    style, _, hue = name.partition("-")
    if style not in STYLES or not hue.isdigit():
        return None

    # Build tint from style and hue
    saturation, brightness = STYLES[style]
    tint = brightness * np.array(
        colorsys.hsv_to_rgb(int(hue) % 360 / 360, saturation, 1.0)
    )

    # Take median grain of originals
    grains = [palette["grain"] for palette in model["palettes"].values()]
    grain = {key: float(np.median([g[key] for g in grains])) for key in grains[0]}
    return dict(tint=tint.tolist(), offset=[0.0, 0.0, 0.0], grain=grain)


def colourise(
    brightness: np.ndarray,
    palette: dict,
    seed: int,
    grain_amount: float,
    grain_size: float,
) -> np.ndarray:
    """Tint brightness field and add grain"""
    height, width = brightness.shape

    # Apply tint
    tint = np.asarray(palette["tint"], float)
    rgb = brightness[..., None] * tint + np.asarray(palette["offset"], float)

    # Add grain
    rng = np.random.default_rng(seed)
    if grain_amount > 0:
        grain = _draw_grain(palette["grain"], width, height, rng, grain_size)
        rgb += (grain * grain_amount)[..., None]

    # Dither where grain cannot hide 8-bit rounding
    if grain_amount * palette["grain"]["uniform_halfwidth"] < DITHER_HALFWIDTH:
        rgb += rng.uniform(-DITHER_HALFWIDTH, DITHER_HALFWIDTH, (height, width, 1))

    # Round to 8 bits
    return np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
