"""Stroke opacity and curve position solve"""

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.interpolate import BSpline
from scipy.sparse.linalg import lsqr

from config import (
    EXTEND_TOP,
    LSQR_TOLERANCE,
    OPACITY_SMOOTH,
    SHIFT_CELL,
    SHIFT_DAMP,
    SHIFT_LIMIT,
    SHIFT_PROBE,
    SHIFT_RESAMPLE_NUDGE,
    SHIFT_RESAMPLE_STEP,
    SHIFT_SMOOTH,
    SPLINE_DEGREE,
    SPLINE_ORDER,
    STROKE_ISOLATION_MARGIN,
    STROKE_ISOLATION_SIGMAS,
    STROKE_ZONE,
)
from field import across_knot_vector, edge_coverage, stroke_coverage, stroke_opacity
from fitting.distances import CurveDistances
from fitting.trace import fit_curve
from splines import basis, clamped_knots, eval_tensor, second_difference


@dataclass
class _StrokePixels:
    """Stroke model evaluated on pixels near strokes"""

    across: np.ndarray
    along: np.ndarray
    opacity: np.ndarray
    cover: np.ndarray
    headroom: np.ndarray
    error: np.ndarray


def _evaluate_strokes(
    brightness: np.ndarray,
    background: np.ndarray,
    distances: CurveDistances,
    model: dict,
) -> _StrokePixels:
    """Evaluate stroke model near strokes"""
    # Select pixels near any stroke
    is_near = (np.abs(distances.across) < STROKE_ZONE).any(axis=0)
    across = distances.across[:, is_near].T
    along = distances.along[:, is_near].T

    # Opacity of every stroke at each pixel
    opacity = np.empty_like(across)
    for k, (curve, (_, arc_lengths)) in enumerate(
        zip(model["curves"], distances.polylines)
    ):
        opacity[:, k] = stroke_opacity(curve, along[:, k], arc_lengths[-1])

    # Combine strokes into coverage
    cover = stroke_coverage(
        across, opacity, model["stroke"]["width"], model["edge_sigma"]
    )

    # Compare painted strokes with observed brightness
    headroom = (model["stroke"]["level"] - background).ravel()[is_near]
    error = (brightness - background).ravel()[is_near] - cover * headroom
    return _StrokePixels(across, along, opacity, cover, headroom, error)


def solve_opacity(
    brightness: np.ndarray,
    background: np.ndarray,
    distances: CurveDistances,
    model: dict,
) -> float:
    """Fit stroke opacity, returns stroke-zone rms error"""
    # Isolation gap from other strokes
    width, level = model["stroke"]["width"], model["stroke"]["level"]
    edge_sigma = model["edge_sigma"]
    isolation = (
        width / 2 + STROKE_ISOLATION_SIGMAS * edge_sigma + STROKE_ISOLATION_MARGIN
    )
    for k, (curve, (_, arc_lengths)) in enumerate(
        zip(model["curves"], distances.polylines)
    ):
        # Pick pixels near this stroke only
        other_gap = np.abs(np.delete(distances.across, k, axis=0)).min(axis=0)
        is_lone = (np.abs(distances.across[k]) < STROKE_ZONE) & (other_gap > isolation)
        along, across = distances.along[k, is_lone], distances.across[k, is_lone]
        observed = (brightness - background).ravel()[is_lone]
        headroom = (level - background).ravel()[is_lone]

        # Weight opacity spline by lone stroke coverage
        count = len(curve["stroke_opacity"])
        indices, weights = basis(
            along, clamped_knots(0, arc_lengths[-1], count - SPLINE_DEGREE)
        )
        profile = edge_coverage(across + width / 2, edge_sigma)
        profile -= edge_coverage(across - width / 2, edge_sigma)
        entries = (np.repeat(np.arange(len(along)), SPLINE_ORDER), indices.ravel())
        design = sp.csr_matrix(
            ((weights * (profile * headroom)[:, None]).ravel(), entries),
            shape=(len(along), count),
        )

        # Solve with roughness penalty
        system = sp.vstack([design, OPACITY_SMOOTH * second_difference(count)])
        targets = np.r_[observed, np.zeros(count - 2)]
        opacity = lsqr(system, targets, atol=LSQR_TOLERANCE, btol=LSQR_TOLERANCE)[0]
        curve["stroke_opacity"] = np.clip(opacity, 0, 1)

    # Score every pixel near a stroke, node included
    error = _evaluate_strokes(brightness, background, distances, model).error
    return np.sqrt((error**2).mean())


def solve_shifts(
    brightness: np.ndarray,
    background: np.ndarray,
    distances: CurveDistances,
    model: dict,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Solve one sub-pixel shift step per curve"""
    # Evaluate strokes and band basis at curve
    width, edge_sigma = model["stroke"]["width"], model["edge_sigma"]
    near = _evaluate_strokes(brightness, background, distances, model)
    edge_basis = basis(np.zeros(len(near.error)), across_knot_vector(model["band"]))
    blocks, penalties, shift_knots = [], [], []
    for k, (curve, (_, arc_lengths)) in enumerate(
        zip(model["curves"], distances.polylines)
    ):
        # Coverage slope by central difference
        probe = np.zeros(len(model["curves"]))
        probe[k] = SHIFT_PROBE
        cover_ahead = stroke_coverage(
            near.across + probe, near.opacity, width, edge_sigma
        )
        cover_behind = stroke_coverage(
            near.across - probe, near.opacity, width, edge_sigma
        )
        cover_slope = (cover_ahead - cover_behind) / (2 * SHIFT_PROBE)

        # Glow edge height under stroke
        along_knots = clamped_knots(0, arc_lengths[-1], curve["along_cells"])
        along_basis = basis(near.along[:, k], along_knots)
        edge_height = eval_tensor(curve["inner"], *along_basis, *edge_basis)
        edge_height -= eval_tensor(curve["outer"], *along_basis, *edge_basis)

        # Edge coverage slope (Gaussian of width edge_sigma)
        edge_slope = np.exp(-0.5 * (near.across[:, k] / edge_sigma) ** 2)
        edge_slope /= edge_sigma * np.sqrt(2 * np.pi)

        # Brightness slope across curve
        slope = (
            cover_slope * near.headroom + (1 - near.cover) * edge_height * edge_slope
        )

        # Shift design block (shift lowers distance across)
        knots = clamped_knots(
            0, arc_lengths[-1], int(round(arc_lengths[-1] / SHIFT_CELL))
        )
        indices, weights = basis(near.along[:, k], knots)
        count = len(knots) - SPLINE_ORDER
        entries = (np.repeat(np.arange(len(slope)), SPLINE_ORDER), indices.ravel())
        blocks.append(
            sp.csr_matrix(
                ((-weights * slope[:, None]).ravel(), entries),
                shape=(len(slope), count),
            )
        )

        # Roughness penalty and damping
        penalties.append(
            sp.vstack(
                [SHIFT_SMOOTH * second_difference(count), SHIFT_DAMP * sp.eye(count)]
            )
        )
        shift_knots.append(knots)

    # Solve all curves together
    system = sp.vstack([sp.hstack(blocks), sp.block_diag(penalties)]).tocsr()
    targets = np.r_[near.error, np.zeros(system.shape[0] - len(near.error))]
    solution = lsqr(system, targets, atol=LSQR_TOLERANCE, btol=LSQR_TOLERANCE)[0]

    # Split solution per curve
    shifts, offset = [], 0
    for knots in shift_knots:
        count = len(knots) - SPLINE_ORDER
        coefficients = np.clip(
            solution[offset : offset + count], -SHIFT_LIMIT, SHIFT_LIMIT
        )
        shifts.append((knots, coefficients))
        offset += count
    return shifts


def shift_curve(
    curve: dict, shift: tuple[np.ndarray, np.ndarray], node_position: float
) -> float:
    """Shift curve along normal, return node position"""
    shift_knots, coefficients = shift
    spline = BSpline(curve["knots"], curve["control_points"], SPLINE_DEGREE)
    length = curve["knots"][-1]

    # Resample curve and its normals
    positions = np.arange(0, length + SHIFT_RESAMPLE_NUDGE, SHIFT_RESAMPLE_STEP)
    tangents = spline.derivative()(positions)
    normals = np.c_[-tangents[:, 1], tangents[:, 0]]
    normals /= np.linalg.norm(tangents, axis=1)[:, None]

    # Move points by shift spline (measured from top extension)
    offsets = BSpline(shift_knots, coefficients, SPLINE_DEGREE)(positions + EXTEND_TOP)
    points = spline(positions) + offsets[:, None] * normals

    # Refit spline through moved points
    node_index = int(np.searchsorted(positions, node_position))
    weights = np.ones(len(points))
    curve["knots"], curve["control_points"], node_position = fit_curve(
        points, weights, node_index
    )
    return node_position
