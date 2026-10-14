"""Original wallpapers and grain measurement"""

import io
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from config import (
    GRAIN_HIGHPASS_SIGMA,
    JPEG_QUALITY,
    JPEG_SUBSAMPLING,
    ORIGINAL_NAME,
)


def find_originals(directory: Path) -> dict[str, Path]:
    """Map colour name to original file"""
    prefix, suffix = ORIGINAL_NAME.split("{}")
    paths = sorted(directory.glob(ORIGINAL_NAME.format("*")))
    return {path.name[len(prefix) : -len(suffix)].lower(): path for path in paths}


def load_image(source: Path | io.BytesIO) -> np.ndarray:
    """Load image as float RGB"""
    return np.asarray(Image.open(source).convert("RGB")).astype(np.float64)


def jpeg_round_trip(image: np.ndarray) -> np.ndarray:
    """Encode and decode like original JPEG"""
    buffer = io.BytesIO()
    Image.fromarray(image).save(
        buffer, "JPEG", quality=JPEG_QUALITY, subsampling=JPEG_SUBSAMPLING
    )
    return load_image(buffer)


def grain_stats(patch: np.ndarray) -> tuple[np.ndarray, float]:
    """Measure grain spread and excess kurtosis"""
    # Remove smooth gradient
    blur = (GRAIN_HIGHPASS_SIGMA, GRAIN_HIGHPASS_SIGMA, 0)
    detail = patch - ndi.gaussian_filter(patch, blur)

    # Spread per channel, kurtosis of channel mean
    mono = detail.mean(axis=2)
    return detail.std(axis=(0, 1)), (mono**4).mean() / mono.var() ** 2 - 3
