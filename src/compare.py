"""Comparison of renders against original wallpapers"""

import argparse
import logging
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from cli import configure_logging
from config import (
    COMPARE_DIR,
    COMPARE_SCALE,
    COMPARE_SEED,
    CROP_CENTRES,
    CROP_SHEET_NAME,
    CROP_SIZE,
    CROP_ZOOM,
    FLAT_PATCH,
    GRAIN_AMOUNT,
    GRAIN_SIZE,
    MODEL_PATH,
    ORIGINAL_NAME,
    ORIGINALS_DIR,
    SHEET_BACKGROUND,
    SHEET_GAP,
    SHEET_LABEL_HEIGHT,
    SHEET_LABEL_INSET,
    SHEET_TEXT,
    STROKE_FREE_COVER,
    STRUCTURE_BLUR,
    WORST_ERROR_BLUR,
)
from field import load_model, render_brightness, render_layers
from originals import find_originals, grain_stats, jpeg_round_trip, load_image
from palettes import colourise

logger = logging.getLogger(__name__)


def _psnr(first: np.ndarray, second: np.ndarray) -> float:
    """Return peak signal-to-noise ratio in dB"""
    return 10 * np.log10(255**2 / np.mean((first - second) ** 2))


def _blur(image: np.ndarray, sigma: float) -> np.ndarray:
    """Blur image within each channel"""
    return ndi.gaussian_filter(image, (sigma, sigma, 0))


def _crop_sheet(original: np.ndarray, render: np.ndarray) -> Image.Image:
    """Lay matching crops side by side"""
    height, width = original.shape[:2]
    scale = render.shape[0] // height

    # Upscale original like a screen
    render_size = (render.shape[1], render.shape[0])
    upscaled = Image.fromarray(original).resize(render_size, Image.BILINEAR)

    # Label original and render columns
    columns = [
        ("original, upscaled to the screen", np.asarray(upscaled)),
        (f"render at {render_size[0]}x{render_size[1]}", render),
    ]

    # Size sheet for two columns of labelled tiles
    tile = CROP_SIZE * scale * CROP_ZOOM
    row_height = tile + SHEET_LABEL_HEIGHT + SHEET_GAP
    sheet_size = (2 * tile + 3 * SHEET_GAP, len(CROP_CENTRES) * row_height + SHEET_GAP)
    sheet = Image.new("RGB", sheet_size, SHEET_BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    for row, (name, (centre_x, centre_y)) in enumerate(CROP_CENTRES.items()):
        # Clamp crop inside frame
        left = int(np.clip(centre_x - CROP_SIZE // 2, 0, width - CROP_SIZE)) * scale
        top = int(np.clip(centre_y - CROP_SIZE // 2, 0, height - CROP_SIZE)) * scale
        span = CROP_SIZE * scale
        for column, (label, image) in enumerate(columns):
            # Paste enlarged crop under its label
            corner_x = SHEET_GAP + column * (tile + SHEET_GAP)
            corner_y = SHEET_GAP + row * row_height
            crop = Image.fromarray(image[top : top + span, left : left + span])
            enlarged = crop.resize((tile, tile), Image.NEAREST)
            sheet.paste(enlarged, (corner_x, corner_y + SHEET_LABEL_HEIGHT))
            label_corner = (corner_x, corner_y + SHEET_LABEL_INSET)
            draw.text(label_corner, f"{name} - {label}", fill=SHEET_TEXT)
    return sheet


def main() -> None:
    """Measure every colour against its original"""
    # Parse arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=ORIGINALS_DIR,
        help="folder holding the originals",
    )
    parser.add_argument(
        "-o", "--outdir", type=Path, default=COMPARE_DIR, help="folder for crop sheets"
    )
    args = parser.parse_args()
    configure_logging()

    # Find originals
    originals = find_originals(args.directory)
    if not originals:
        parser.error(f"no '{ORIGINAL_NAME.format('*')}' in {args.directory}")
    args.outdir.mkdir(exist_ok=True)

    # Render brightness at original and comparison size
    model = load_model(MODEL_PATH)
    width, height = model["design_size"]
    brightness = render_brightness(model, width, height)
    is_stroke_free = render_layers(model, width, height)[1] < STROKE_FREE_COVER
    large_size = (width * COMPARE_SCALE, height * COMPARE_SCALE)
    large_brightness = render_brightness(model, *large_size)

    # Log column headings
    logger.info(
        "colour   PSNR without grain    PSNR, %dpx blur   worst error, %dpx blur"
        "   mean colour error    grain std",
        STRUCTURE_BLUR,
        WORST_ERROR_BLUR,
    )
    logger.info(
        "         (ceiling from grain)  (with grain)     (levels)               "
        " (levels, max chan)   original / render"
    )
    for colour, path in originals.items():
        # Load palette and original
        palette = model["palettes"][colour]
        original = load_image(path)

        # Render with and without grain
        tint, offset = np.asarray(palette["tint"]), np.asarray(palette["offset"])
        clean = brightness[..., None] * tint + offset
        grainy = jpeg_round_trip(
            colourise(brightness, palette, COMPARE_SEED, GRAIN_AMOUNT, GRAIN_SIZE)
        )

        # Ceiling set by original grain alone
        ceiling = 20 * np.log10(255 / (original - clean)[is_stroke_free].std())

        # Structure with grain blurred away
        structure_psnr = _psnr(
            _blur(original, STRUCTURE_BLUR), _blur(grainy, STRUCTURE_BLUR)
        )
        worst_error = np.abs(
            _blur(original, WORST_ERROR_BLUR) - _blur(grainy, WORST_ERROR_BLUR)
        ).max()

        # Mean colour and grain spread
        colour_error = np.abs(
            original.mean(axis=(0, 1)) - grainy.mean(axis=(0, 1))
        ).max()
        original_spread = grain_stats(original[FLAT_PATCH])[0].mean()
        render_spread = grain_stats(grainy[FLAT_PATCH])[0].mean()

        # Log this colour's figures
        logger.info(
            "%-8s %5.2f dB (%5.2f dB)     %5.2f dB         %4.2f                 "
            "   %4.2f                 %.2f / %.2f",
            colour,
            _psnr(original, clean),
            ceiling,
            structure_psnr,
            worst_error,
            colour_error,
            original_spread,
            render_spread,
        )

        # Save side-by-side crops
        large = colourise(
            large_brightness, palette, COMPARE_SEED, GRAIN_AMOUNT, GRAIN_SIZE
        )
        sheet = _crop_sheet(original.astype(np.uint8), large)
        sheet.save(args.outdir / CROP_SHEET_NAME.format(colour))
    logger.info("wrote %s", args.outdir / CROP_SHEET_NAME.format("<colour>"))


if __name__ == "__main__":
    main()
