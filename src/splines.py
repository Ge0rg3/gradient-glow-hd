"""Cubic B-spline helpers"""

import numpy as np
import scipy.sparse as sp
from scipy.interpolate import BSpline

from config import EVAL_CHUNK, SPLINE_DEGREE, SPLINE_ORDER


def clamped_knots(start: float, end: float, cells: int) -> np.ndarray:
    """Build clamped uniform knot vector"""
    interior = np.linspace(start, end, cells + 1)
    return np.r_[[start] * SPLINE_DEGREE, interior, [end] * SPLINE_DEGREE]


def basis(positions: np.ndarray, knots: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return active basis indices and weights"""
    # Evaluate basis at clamped positions (design_matrix raises outside knot span)
    clamped = np.clip(np.asarray(positions, dtype=float), knots[0], knots[-1])
    design = BSpline.design_matrix(clamped, knots, SPLINE_DEGREE).tocsr()

    # Unpack SPLINE_ORDER entries per row
    indices = design.indices.reshape(-1, SPLINE_ORDER)
    weights = design.data.reshape(-1, SPLINE_ORDER)
    return indices, weights


def eval_tensor(
    table: np.ndarray,
    row_indices: np.ndarray,
    row_weights: np.ndarray,
    column_indices: np.ndarray,
    column_weights: np.ndarray,
) -> np.ndarray:
    """Evaluate tensor-product spline per point"""
    # Evaluate points in chunks
    heights = np.empty(len(row_indices))
    for start in range(0, len(row_indices), EVAL_CHUNK):
        chunk = slice(start, start + EVAL_CHUNK)
        rows = row_indices[chunk][:, :, None]
        columns = column_indices[chunk][:, None, :]

        # Sum weighted coefficients per point
        heights[chunk] = np.einsum(
            "nab,na,nb->n",
            table[rows, columns],
            row_weights[chunk],
            column_weights[chunk],
        )
    return heights


def second_difference(count: int) -> sp.spmatrix:
    """Build second difference operator"""
    return sp.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(count - 2, count))
