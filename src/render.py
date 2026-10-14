"""Wallpaper renderer for any resolution"""

import argparse
import logging
from pathlib import Path

from PIL import Image

from cli import configure_logging, parse_size
from config import (
    DEFAULT_SIZE,
    GRAIN_AMOUNT,
    GRAIN_SEED,
    GRAIN_SIZE,
    MODEL_PATH,
    RENDER_NAME,
    SIZE_HELP,
    STYLES,
)
from field import load_model, render_brightness
from palettes import colourise, find_palette

logger = logging.getLogger(__name__)


def main() -> None:
    """Render requested colours"""
    # Parse arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "colours",
        nargs="*",
        help="originals by name, or <style>-<hue> with a style from "
        f"{', '.join(STYLES)} and a hue of 0-359 (default: every original)",
    )
    parser.add_argument(
        "-s", "--size", default=DEFAULT_SIZE, type=parse_size, help=SIZE_HELP
    )
    parser.add_argument(
        "-d", "--outdir", type=Path, default=Path("."), help="folder to write into"
    )
    parser.add_argument(
        "-n",
        "--name",
        default=RENDER_NAME,
        help="file name pattern filling {colour}, {Colour}, {width} and {height} "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "--grain",
        type=float,
        default=GRAIN_AMOUNT,
        help="grain strength, 1 matches the originals and 0 turns it off",
    )
    parser.add_argument(
        "--grain-size",
        type=float,
        default=GRAIN_SIZE,
        help="grain cell size in output pixels (default: %(default)s)",
    )
    parser.add_argument(
        "--seed", type=int, default=GRAIN_SEED, help="grain random seed"
    )
    args = parser.parse_args()
    configure_logging()

    # Resolve palettes
    model = load_model(MODEL_PATH)
    colours = [colour.lower() for colour in args.colours] or list(model["palettes"])
    palettes = {colour: find_palette(model, colour) for colour in colours}
    unknown = [colour for colour, palette in palettes.items() if palette is None]
    if unknown:
        parser.error(
            f"unknown colour {', '.join(unknown)}, use one of "
            f"{', '.join(model['palettes'])} or <style>-<hue> with a style from "
            f"{', '.join(STYLES)}"
        )

    # Render brightness once for every colour
    width, height = args.size
    brightness = render_brightness(model, width, height)

    # Colour and save
    args.outdir.mkdir(parents=True, exist_ok=True)
    for colour, palette in palettes.items():
        name = args.name.format(
            colour=colour, Colour=colour.capitalize(), width=width, height=height
        )
        image = colourise(brightness, palette, args.seed, args.grain, args.grain_size)
        Image.fromarray(image).save(args.outdir / name, optimize=True)
        logger.info("wrote %s", args.outdir / name)


if __name__ == "__main__":
    main()
