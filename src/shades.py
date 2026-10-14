"""Shade wallpapers and their gallery page"""

import argparse
import colorsys
import html
import logging
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

from cli import configure_logging, parse_size
from config import (
    DEFAULT_SIZE,
    GALLERY_ASSETS,
    GALLERY_DIR,
    GALLERY_HUES,
    GALLERY_PAGE,
    GALLERY_TEMPLATE,
    GALLERY_WORKERS,
    GRAIN_AMOUNT,
    GRAIN_SEED,
    GRAIN_SIZE,
    HUE_PROBE_BRIGHTNESS,
    HUE_PROBE_STYLE,
    HUE_STEP,
    MODEL_PATH,
    OKLAB_A,
    OKLAB_B,
    OKLAB_CONES,
    SIZE_HELP,
    SRGB_GAMMA,
    SRGB_LINEAR_LIMIT,
    SRGB_LINEAR_SLOPE,
    SRGB_OFFSET,
    STYLE_BLURBS,
    STYLES,
    THUMB_DIR,
    THUMB_QUALITY,
    THUMB_SIZE,
)
from field import load_model, render_brightness
from palettes import colourise, find_palette

logger = logging.getLogger(__name__)

# Brightness field of each worker (pool workers start without parent state)
_worker_brightness = None


def _oklab_hue(rgb: np.ndarray) -> np.ndarray:
    """Return perceptual hue angle in degrees"""
    # Undo sRGB gamma
    curved = ((rgb + SRGB_OFFSET) / (1 + SRGB_OFFSET)) ** SRGB_GAMMA
    linear = np.where(rgb <= SRGB_LINEAR_LIMIT, rgb / SRGB_LINEAR_SLOPE, curved)

    # Convert to OKLab a and b
    cones = np.cbrt(linear @ np.array(OKLAB_CONES))
    green_red, blue_yellow = cones @ np.array(OKLAB_A), cones @ np.array(OKLAB_B)
    return np.degrees(np.arctan2(blue_yellow, green_red)) % 360


def _even_hues(count: int) -> list[int]:
    """Pick HSV hues evenly spaced to the eye"""
    saturation, brightness = STYLES[HUE_PROBE_STYLE]
    hsv_hues = np.arange(0, 360, HUE_STEP)

    # Measure perceptual hue of each HSV hue
    probe = brightness * HUE_PROBE_BRIGHTNESS
    colours = np.array(
        [colorsys.hsv_to_rgb(hue / 360, saturation, probe) for hue in hsv_hues]
    )
    seen_hues = np.degrees(np.unwrap(np.radians(_oklab_hue(colours))))

    # Invert at even perceptual steps
    targets = seen_hues[0] + np.arange(count) * 360 / count
    even_hues = np.interp(targets, seen_hues, hsv_hues)
    return sorted(int(round(hue)) % 360 for hue in even_hues)


def _share_brightness(brightness: np.ndarray) -> None:
    """Store brightness field in worker process"""
    global _worker_brightness
    _worker_brightness = brightness


def _paint_shade(job: tuple[str, dict, Path]) -> str:
    """Save one shade and its thumbnail"""
    # Colour and save shade
    name, palette, outdir = job
    pixels = colourise(
        _worker_brightness, palette, GRAIN_SEED, GRAIN_AMOUNT, GRAIN_SIZE
    )
    image = Image.fromarray(pixels)
    image.save(outdir / f"{name}.png", optimize=True)

    # Save thumbnail
    thumb = image.resize(THUMB_SIZE, Image.LANCZOS)
    thumb.save(outdir / THUMB_DIR / f"{name}.jpg", quality=THUMB_QUALITY)
    return name


def _build_page(
    groups: list[tuple[str, str, list[str]]], width: int, height: int
) -> str:
    """Fill gallery template"""
    sections = []
    for title, blurb, names in groups:
        # One tile per shade
        tiles = "\n".join(
            f'  <figure class="tile" data-name="{name}">'
            f'<img src="{THUMB_DIR}/{name}.jpg" alt="{name}">'
            f"<figcaption>{name}</figcaption></figure>"
            for name in names
        )

        # Add heading and grid
        heading = f"<h2>{html.escape(title)}<span>{html.escape(blurb)}</span></h2>"
        sections.append(f'{heading}\n<div class="grid">\n{tiles}\n</div>')

    # Fill template
    shade_count = sum(len(names) for _, _, names in groups)
    return GALLERY_TEMPLATE.read_text().format(
        count=shade_count, width=width, height=height, sections="\n".join(sections)
    )


def main() -> None:
    """Render every style at a ring of hues"""
    # Parse arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-s", "--size", default=DEFAULT_SIZE, type=parse_size, help=SIZE_HELP
    )
    parser.add_argument(
        "-d", "--outdir", type=Path, default=GALLERY_DIR, help="folder to write into"
    )
    parser.add_argument(
        "--hues",
        type=int,
        default=GALLERY_HUES,
        help="hues per style (default: %(default)s)",
    )
    args = parser.parse_args()
    configure_logging()

    # List originals then every style at each hue
    model = load_model(MODEL_PATH)
    hues = _even_hues(args.hues)
    groups = [("originals", "for reference", list(model["palettes"]))]
    for style in STYLES:
        shades = [f"{style}-{hue}" for hue in hues]
        groups.append((style, STYLE_BLURBS[style], shades))
    names = [name for _, _, group_names in groups for name in group_names]

    # Render brightness once for every shade
    width, height = args.size
    brightness = render_brightness(model, width, height)

    # Paint shades in parallel
    (args.outdir / THUMB_DIR).mkdir(parents=True, exist_ok=True)
    jobs = [(name, find_palette(model, name), args.outdir) for name in names]
    with ProcessPoolExecutor(
        max_workers=GALLERY_WORKERS,
        initializer=_share_brightness,
        initargs=(brightness,),
    ) as pool:
        painted = list(pool.map(_paint_shade, jobs))

    # Write gallery page and its assets
    page = args.outdir / GALLERY_PAGE
    page.write_text(_build_page(groups, width, height))
    for asset in GALLERY_ASSETS:
        shutil.copy(asset, args.outdir)
    logger.info("wrote %d shades and %s", len(painted), page)


if __name__ == "__main__":
    main()
