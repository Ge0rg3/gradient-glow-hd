"""Brightness field of the design"""

import json
from pathlib import Path

import numpy as np
from scipy.interpolate import BSpline
from scipy.special import erf

from config import OUT_OF_REACH, SPLINE_DEGREE, SPLINE_ORDER, STROKE_REACH_SIGMAS
from curves import flatten, pixels_near, project
from splines import basis, clamped_knots, eval_tensor


def _pixel_grid(
    model: dict, width: int, height: int
) -> tuple[np.ndarray, np.ndarray, float]:
    """Map output pixel centres to design space"""
    design_width, design_height = model["design_size"]

    # Scale design to cover output (other aspect ratios crop)
    scale = max(width / design_width, height / design_height)

    # Centre output on design (design pixel centres are whole numbers)
    xs = (np.arange(width) + 0.5 - width / 2) / scale + design_width / 2 - 0.5
    ys = (np.arange(height) + 0.5 - height / 2) / scale + design_height / 2 - 0.5
    return xs, ys, scale


def _lighting(model: dict, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Evaluate lighting lattice at pixel centres"""
    design_width, design_height = model["design_size"]
    cells_x, cells_y = model["lattice"]["cells"]
    coefficients = np.asarray(model["lattice"]["coefficients"], float)

    # Pixel centres span -0.5 to size - 0.5
    knots_x = clamped_knots(-0.5, design_width - 0.5, cells_x)
    knots_y = clamped_knots(-0.5, design_height - 0.5, cells_y)

    # Evaluate basis along each axis
    basis_x = BSpline.design_matrix(xs, knots_x, SPLINE_DEGREE)
    basis_y = BSpline.design_matrix(ys, knots_y, SPLINE_DEGREE)
    return basis_y @ (basis_x @ coefficients.T).T


def load_model(path: Path) -> dict:
    """Load model description"""
    return json.loads(path.read_text())


def across_knot_vector(band: dict) -> np.ndarray:
    """Build band knot vector across curve"""
    radius = band["radius"]
    return np.r_[[0.0] * SPLINE_DEGREE, band["across_knots"], [radius] * SPLINE_ORDER]


def edge_coverage(across: np.ndarray, sigma: float) -> np.ndarray:
    """Anti-alias unit step across curve"""
    return 0.5 * (1 + erf(across / (np.sqrt(2) * sigma)))


def stroke_opacity(curve: dict, along: np.ndarray, length: float) -> np.ndarray:
    """Evaluate stroke opacity along curve"""
    coefficients = np.asarray(curve["stroke_opacity"], float)
    knots = clamped_knots(0, length, len(coefficients) - SPLINE_DEGREE)
    indices, weights = basis(along, knots)
    return (weights * coefficients[indices]).sum(1)


def stroke_coverage(
    across: np.ndarray, opacity: np.ndarray, width: float, sigma: float
) -> np.ndarray:
    """Combine stroke opacities per pixel"""
    # Stroke extents along shared normal
    lower, upper = -across - width / 2, -across + width / 2

    # Slice at every stroke edge
    cuts = np.sort(np.concatenate([lower, upper], axis=1), axis=1)
    middles = 0.5 * (cuts[:, 1:] + cuts[:, :-1])

    # Take most opaque stroke per slice (crossing strokes do not accumulate)
    is_above_lower = lower[:, None, :] < middles[:, :, None]
    is_below_upper = middles[:, :, None] < upper[:, None, :]
    opaquest = (opacity[:, None, :] * (is_above_lower & is_below_upper)).max(axis=2)

    # Sum slice coverage weighted by opacity
    return (opaquest * np.diff(edge_coverage(cuts, sigma), axis=1)).sum(axis=1)


def render_layers(
    model: dict, width: int, height: int
) -> tuple[np.ndarray, np.ndarray]:
    """Render background and stroke coverage"""
    xs, ys, scale = _pixel_grid(model, width, height)

    # Edge softness in design px (constant in output px)
    edge_sigma = model["edge_sigma"] / scale
    stroke_width = model["stroke"]["width"]
    stroke_reach = stroke_width / 2 + STROKE_REACH_SIGMAS * edge_sigma
    radius = model["band"]["radius"]
    across_knots = across_knot_vector(model["band"])

    # Start background from lighting
    background = _lighting(model, xs, ys).ravel()
    strokes = []
    for curve in model["curves"]:
        # Project nearby pixels onto curve
        polyline, arc_lengths = flatten(curve)
        nearby = pixels_near(polyline, xs, ys, radius)
        centres = np.c_[xs[nearby % width], ys[nearby // width]]
        within, along, across = project(polyline, arc_lengths, centres, radius)
        pixels = nearby[within]

        # Evaluate glow band on each side
        along_knots = clamped_knots(0, arc_lengths[-1], curve["along_cells"])
        along_basis = basis(along, along_knots)
        inner_basis = basis(np.maximum(across, 0), across_knots)
        outer_basis = basis(np.maximum(-across, 0), across_knots)
        inner_table = np.asarray(curve["inner"], float)
        outer_table = np.asarray(curve["outer"], float)
        inner = eval_tensor(inner_table, *along_basis, *inner_basis)
        outer = eval_tensor(outer_table, *along_basis, *outer_basis)

        # Blend sides across crisp edge
        inner_share = edge_coverage(across, edge_sigma)
        background[pixels] += inner_share * inner + (1 - inner_share) * outer

        # Collect stroke opacity near curve
        is_inked = np.abs(across) < stroke_reach
        opacity = stroke_opacity(curve, along[is_inked], arc_lengths[-1])
        strokes.append((pixels[is_inked], across[is_inked], np.clip(opacity, 0, 1)))

    # Tabulate every stroke per inked pixel
    inked = np.unique(np.concatenate([pixels for pixels, _, _ in strokes]))
    across_table = np.full((len(inked), len(strokes)), OUT_OF_REACH)
    opacity_table = np.zeros((len(inked), len(strokes)))
    for column, (pixels, across, opacity) in enumerate(strokes):
        rows = np.searchsorted(inked, pixels)
        across_table[rows, column], opacity_table[rows, column] = across, opacity

    # Combine strokes
    stroke_cover = np.zeros(width * height)
    stroke_cover[inked] = stroke_coverage(
        across_table, opacity_table, stroke_width, edge_sigma
    )
    return background.reshape(height, width), stroke_cover.reshape(height, width)


def render_brightness(model: dict, width: int, height: int) -> np.ndarray:
    """Render grain-free brightness field"""
    background, stroke_cover = render_layers(model, width, height)

    # Paint strokes over background
    return background + stroke_cover * (model["stroke"]["level"] - background)
