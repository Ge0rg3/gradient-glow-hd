"""Curve polylines and closest-point projection"""

import numpy as np
from scipy.interpolate import BSpline
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

from config import (
    COARSE_CELL,
    COARSE_SLACK_CELLS,
    FLATTEN_STEP,
    PROJECT_SLACK,
    SPLINE_DEGREE,
)


def flatten(curve: dict) -> tuple[np.ndarray, np.ndarray]:
    """Flatten curve into polyline and arc lengths"""
    # Build curve spline
    knots = np.asarray(curve["knots"], float)
    control_points = np.asarray(curve["control_points"], float)
    spline = BSpline(knots, control_points, SPLINE_DEGREE, extrapolate=True)
    length = knots[-1]

    # Sample spline (polynomial continuation above frame)
    positions = np.arange(-curve["extend_top"], length + FLATTEN_STEP / 2, FLATTEN_STEP)
    polyline = spline(positions)

    # Extend tail along end tangent
    tangent = spline.derivative()(length)
    tangent /= np.linalg.norm(tangent)
    extension = np.arange(
        FLATTEN_STEP, curve["extend_tail"] + FLATTEN_STEP / 2, FLATTEN_STEP
    )
    polyline = np.vstack([polyline, polyline[-1] + extension[:, None] * tangent])

    # Accumulate arc length
    steps = np.linalg.norm(np.diff(polyline, axis=0), axis=1)
    return polyline, np.r_[0, np.cumsum(steps)]


def project(
    polyline: np.ndarray, arc_lengths: np.ndarray, points: np.ndarray, radius: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Project points onto polyline within radius"""
    # Find nearest vertex
    tree = cKDTree(polyline)
    gap, vertex = tree.query(
        points, distance_upper_bound=radius + PROJECT_SLACK, workers=-1
    )
    is_inside = np.isfinite(gap) & (vertex > 0) & (vertex < len(polyline) - 1)
    vertex, inside_points = vertex[is_inside], points[is_inside]

    # Refine on both adjoining segments
    best_sq = np.full(len(vertex), np.inf)
    along = np.zeros(len(vertex))
    across = np.zeros(len(vertex))
    for first in (vertex - 1, vertex):
        start = polyline[first]
        segment = polyline[first + 1] - start
        segment_sq = (segment**2).sum(1)
        fraction = np.clip(
            ((inside_points - start) * segment).sum(1) / segment_sq, 0, 1
        )
        offset = inside_points - (start + fraction[:, None] * segment)
        offset_sq = (offset**2).sum(1)

        # Sign distance positive on inner side
        side = np.sign(segment[:, 0] * offset[:, 1] - segment[:, 1] * offset[:, 0])

        # Keep closer segment
        is_closer = offset_sq < best_sq
        best_sq[is_closer] = offset_sq[is_closer]
        along[is_closer] = (arc_lengths[first] + fraction * np.sqrt(segment_sq))[
            is_closer
        ]
        across[is_closer] = (side * np.sqrt(offset_sq))[is_closer]

    # Keep points within radius
    is_within = np.abs(across) <= radius
    return np.flatnonzero(is_inside)[is_within], along[is_within], across[is_within]


def pixels_near(
    polyline: np.ndarray, xs: np.ndarray, ys: np.ndarray, radius: float
) -> np.ndarray:
    """Return flat indices of pixels near polyline"""
    # Lay coarse grid over frame (padded for off-frame vertices in reach)
    left, top = xs[0] - COARSE_CELL, ys[0] - COARSE_CELL
    columns = int((xs[-1] - left) / COARSE_CELL) + 1 + COARSE_SLACK_CELLS
    rows = int((ys[-1] - top) / COARSE_CELL) + 1 + COARSE_SLACK_CELLS
    margin = int(radius / COARSE_CELL) + COARSE_SLACK_CELLS

    # Mark cells containing polyline vertices
    cell_x = ((polyline[:, 0] - left) / COARSE_CELL).astype(int)
    cell_y = ((polyline[:, 1] - top) / COARSE_CELL).astype(int)
    is_on_grid = (
        (cell_x >= -margin)
        & (cell_x < columns + margin)
        & (cell_y >= -margin)
        & (cell_y < rows + margin)
    )
    is_empty = np.ones((rows + 2 * margin, columns + 2 * margin), bool)
    is_empty[cell_y[is_on_grid] + margin, cell_x[is_on_grid] + margin] = False

    # Keep cells within reach
    reach = distance_transform_edt(is_empty) * COARSE_CELL
    slack = COARSE_SLACK_CELLS * COARSE_CELL
    is_close = (reach <= radius + slack)[margin:-margin, margin:-margin]

    # Look up each pixel's cell
    pixel_x = ((xs - left) / COARSE_CELL).astype(int)
    pixel_y = ((ys - top) / COARSE_CELL).astype(int)
    return np.flatnonzero(is_close[pixel_y[:, None], pixel_x[None, :]])
