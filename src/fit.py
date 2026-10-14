"""Wallpaper model fit from original JPEGs"""

import argparse
import json
import logging
from pathlib import Path

import numpy as np

from cli import configure_logging
from config import (
    BAND_ACROSS_KNOTS,
    BAND_ALONG_CELL,
    BAND_RADIUS,
    EDGE_SIGMA,
    EDGE_SIGMA_GRID,
    EXTEND_TAIL,
    EXTEND_TOP,
    FIT_ITERATIONS,
    LATTICE_CELL,
    MODEL_DECIMALS,
    MODEL_PATH,
    MODEL_PRECISE_DECIMALS,
    MODEL_PRECISE_KEYS,
    OPACITY_CELL,
    ORIGINAL_NAME,
    ORIGINALS_DIR,
    REFERENCE_COLOUR,
    SEARCH_ROUNDS,
    SPLINE_DEGREE,
    STROKE_LEVEL,
    STROKE_LEVEL_GRID,
    STROKE_WIDTH,
    STROKE_WIDTH_GRID,
    TRACE_MAX_WEIGHT,
)
from field import load_model, render_brightness, render_layers
from fitting.distances import CurveDistances
from fitting.grain import calibrate_grain, remove_grain
from fitting.smooth import solve_background
from fitting.strokes import shift_curve, solve_opacity, solve_shifts
from fitting.trace import fit_curve, trace_curves
from originals import find_originals, load_image

logger = logging.getLogger(__name__)


def _prepare_background(
    model: dict, target: np.ndarray
) -> tuple[CurveDistances, np.ndarray]:
    """Solve background for current curves"""
    # Project pixels onto curves
    height, width = target.shape
    distances = CurveDistances(model["curves"], target.shape)

    # Size band and opacity splines to curve length
    for curve, (_, arc_lengths) in zip(model["curves"], distances.polylines):
        opacity_cells = int(round(arc_lengths[-1] / OPACITY_CELL))
        curve["along_cells"] = int(round(arc_lengths[-1] / BAND_ALONG_CELL))
        curve["stroke_opacity"] = np.zeros(opacity_cells + SPLINE_DEGREE)

    # Solve and render background
    solve_background(target, distances, model)
    return distances, render_layers(model, width, height)[0]


def _stroke_error(
    brightness: np.ndarray, distances: CurveDistances, model: dict
) -> float:
    """Refit stroke opacity, returns stroke-zone rms error"""
    height, width = brightness.shape
    background = render_layers(model, width, height)[0]
    return solve_opacity(brightness, background, distances, model)


def _fit_shape(rgb: np.ndarray, iterations: int) -> dict:
    """Fit colour-independent shape from one original"""
    # Remove grain
    height, width = rgb.shape[:2]
    tint, brightness = remove_grain(rgb)
    logger.info("tint (G = 1): %s", tint.round(4))

    # Background target from green plus blue (red banding four times coarser)
    soft_target = (rgb[..., 1] + rgb[..., 2]) / (tint[1] + tint[2])

    # Trace curves and fit splines
    curves, node_positions = [], []
    for upper, lower in trace_curves(brightness):
        points = np.vstack([upper[:, :2], lower[:, :2]])
        weights = np.clip(np.r_[upper[:, 2], lower[:, 2]], 0, TRACE_MAX_WEIGHT)
        knots, control_points, node_position = fit_curve(points, weights, len(upper))
        curves.append(
            dict(
                knots=knots,
                control_points=control_points,
                extend_top=EXTEND_TOP,
                extend_tail=EXTEND_TAIL,
            )
        )
        node_positions.append(node_position)

    # Build model with starting settings
    model = dict(
        design_size=[width, height],
        edge_sigma=EDGE_SIGMA,
        stroke=dict(width=STROKE_WIDTH, level=STROKE_LEVEL),
        band=dict(radius=BAND_RADIUS, across_knots=BAND_ACROSS_KNOTS),
        lattice=dict(cells=[int(width / LATTICE_CELL), int(height / LATTICE_CELL)]),
        curves=curves,
    )

    # Alternate background solve and curve shifts
    for iteration in range(iterations):
        distances, background = _prepare_background(model, soft_target)
        rms = solve_opacity(brightness, background, distances, model)
        shifts = solve_shifts(brightness, background, distances, model)
        shift_sizes = [np.mean(coefficients**2) for _, coefficients in shifts]
        logger.info(
            "iteration %d: stroke-zone rms %.3f, rms curve shift %.3f px",
            iteration + 1,
            rms,
            np.sqrt(np.mean(shift_sizes)),
        )
        for k, (curve, shift) in enumerate(zip(curves, shifts)):
            node_positions[k] = shift_curve(curve, shift, node_positions[k])

    # Solve background for final curves
    distances, _ = _prepare_background(model, soft_target)

    # Search stroke level, width and edge softness in turn
    searched = [
        (model["stroke"], "level", STROKE_LEVEL_GRID),
        (model["stroke"], "width", STROKE_WIDTH_GRID),
        (model, "edge_sigma", EDGE_SIGMA_GRID),
    ]
    best_rms = _stroke_error(brightness, distances, model)
    for _ in range(SEARCH_ROUNDS):
        for settings, key, grid in searched:
            best_setting = settings[key]
            for candidate in np.arange(*grid):
                settings[key] = float(candidate)
                rms = _stroke_error(brightness, distances, model)
                if rms < best_rms:
                    best_rms, best_setting = rms, float(candidate)
            settings[key] = best_setting

    # Refit opacity at chosen settings
    rms = _stroke_error(brightness, distances, model)
    logger.info(
        "stroke level %.0f, width %.2f px, edge sigma %.2f px, stroke-zone rms %.3f",
        model["stroke"]["level"],
        model["stroke"]["width"],
        model["edge_sigma"],
        rms,
    )
    return model


def _fit_palette(rgb: np.ndarray, brightness: np.ndarray) -> dict:
    """Fit tint, offset and grain of one colour"""
    # Least squares tint and offset per channel
    design = np.c_[brightness.ravel(), np.ones(brightness.size)]
    tint, offset = np.linalg.lstsq(design, rgb.reshape(-1, 3), rcond=None)[0]

    # Calibrate grain
    grain = calibrate_grain(rgb, brightness[..., None] * tint + offset)
    return dict(tint=tint, offset=offset, grain=grain)


def _round_for_json(node: object, decimals: int) -> object:
    """Round arrays and floats for JSON"""
    if isinstance(node, dict):
        return {
            key: _round_for_json(
                child, MODEL_PRECISE_DECIMALS if key in MODEL_PRECISE_KEYS else decimals
            )
            for key, child in node.items()
        }
    if isinstance(node, np.ndarray):
        return np.round(node, decimals).tolist()
    if isinstance(node, list):
        return [_round_for_json(child, decimals) for child in node]
    if isinstance(node, float):
        return round(node, decimals)
    return node


def main() -> None:
    """Fit model and write it"""
    # Parse arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=ORIGINALS_DIR,
        help="folder holding the 1920x1080 "
        f"'{ORIGINAL_NAME.format('<Colour>')}' originals",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=MODEL_PATH, help="model file to write"
    )
    parser.add_argument(
        "--reference",
        default=REFERENCE_COLOUR,
        help="colour the shape is measured from (default: %(default)s)",
    )
    parser.add_argument(
        "--keep-shape",
        dest="should_keep_shape",
        action="store_true",
        help="keep the shape in the model file and refit only the palettes",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=FIT_ITERATIONS,
        help="curve position passes (default: %(default)s)",
    )
    args = parser.parse_args()
    configure_logging()

    # Find originals
    originals = find_originals(args.directory)
    if not originals:
        parser.error(f"no '{ORIGINAL_NAME.format('*')}' in {args.directory}")

    # Reuse shape or fit it from reference colour
    if args.should_keep_shape:
        model = load_model(args.output)
    elif args.reference in originals:
        model = _fit_shape(load_image(originals[args.reference]), args.iterations)
    else:
        reference = ORIGINAL_NAME.format(args.reference.capitalize())
        parser.error(f"no '{reference}' in {args.directory}")

    # Fit palette per colour
    brightness = render_brightness(model, *model["design_size"])
    model["palettes"] = {}
    for colour, path in originals.items():
        palette = _fit_palette(load_image(path), brightness)
        model["palettes"][colour] = palette
        logger.info(
            "%-7s tint %s  grain +-%.2f, sigma %.1f",
            colour,
            np.round(palette["tint"], 3),
            palette["grain"]["uniform_halfwidth"],
            palette["grain"]["gauss_sigma"],
        )

    # Write model
    rounded = _round_for_json(model, MODEL_DECIMALS)
    args.output.write_text(json.dumps(rounded, separators=(",", ":")))
    logger.info("wrote %s (%.0f kB)", args.output, args.output.stat().st_size / 1024)


if __name__ == "__main__":
    main()
