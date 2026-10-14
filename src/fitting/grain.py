"""Grain removal and calibration"""

import numpy as np
from scipy import ndimage as ndi

from config import (
    CALIBRATION_SEED,
    FLAT_PATCH,
    GRAIN_HALFWIDTHS,
    GRAIN_KURTOSIS_TOLERANCE,
    GRAIN_SIGMAS,
    GRAIN_SPREAD_TOLERANCE,
    TINT_BLUR_SIGMA,
    TINT_STRIDE,
)
from originals import grain_stats, jpeg_round_trip


def remove_grain(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return tint and grain-free brightness"""
    # Estimate tint axis from blurred pixels
    blurred = ndi.gaussian_filter(rgb, (TINT_BLUR_SIGMA, TINT_BLUR_SIGMA, 0))
    sampled = blurred.reshape(-1, 3)[::TINT_STRIDE]
    axis = np.linalg.svd(sampled, full_matrices=False)[2][0]

    # Scale tint so brightness is in green levels
    tint = axis / axis[1]

    # Project out grey (grain is identical in R, G and B)
    chroma = tint - tint.mean()
    return tint, rgb @ chroma / (chroma @ chroma)


def calibrate_grain(original: np.ndarray, clean: np.ndarray) -> dict:
    """Find grain matching original after JPEG"""
    # Measure original grain
    target_spread, target_kurtosis = grain_stats(original[FLAT_PATCH])

    # Draw unit noise once
    rng = np.random.default_rng(CALIBRATION_SEED)
    uniform = rng.uniform(-1, 1, clean[FLAT_PATCH].shape[:2])
    normal = rng.normal(0, 1, uniform.shape)

    # Score each candidate after 8-bit rounding and JPEG
    best = (np.inf, 0.0, 0.0)
    for sigma in GRAIN_SIGMAS:
        for halfwidth in np.arange(*GRAIN_HALFWIDTHS):
            grain = (halfwidth * uniform + sigma * normal)[..., None]
            rounded = np.clip(np.rint(clean[FLAT_PATCH] + grain), 0, 255)
            spread, kurtosis = grain_stats(jpeg_round_trip(rounded.astype(np.uint8)))
            spread_miss = (
                spread.mean() - target_spread.mean()
            ) / GRAIN_SPREAD_TOLERANCE
            kurtosis_miss = (kurtosis - target_kurtosis) / GRAIN_KURTOSIS_TOLERANCE
            miss = spread_miss**2 + kurtosis_miss**2
            best = min(best, (miss, float(halfwidth), float(sigma)))
    return dict(uniform_halfwidth=best[1], gauss_sigma=best[2])
