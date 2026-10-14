"""Lighting lattice and glow band solve"""

import numpy as np
import scipy.sparse as sp
from scipy.linalg import cho_factor, cho_solve

from config import (
    BAND_PINNED,
    BAND_RIDGE,
    BAND_SMOOTH_ACROSS,
    BAND_SMOOTH_ALONG,
    LATTICE_RIDGE,
    SPLINE_DEGREE,
    SPLINE_ORDER,
    STROKE_MASK,
)
from field import across_knot_vector
from fitting.distances import CurveDistances
from splines import basis, clamped_knots, second_difference


def _tensor_design(
    rows: np.ndarray,
    first_basis: tuple[np.ndarray, np.ndarray],
    second_basis: tuple[np.ndarray, np.ndarray],
    second_count: int,
    shape: tuple[int, int],
) -> sp.csr_matrix:
    """Build sparse tensor-product design matrix"""
    first_indices, first_weights = first_basis
    second_indices, second_weights = second_basis
    terms = SPLINE_ORDER**2

    # Column per coefficient pair, weight per basis product
    columns = first_indices[:, :, None] * second_count + second_indices[:, None, :]
    weights = first_weights[:, :, None] * second_weights[:, None, :]
    entries = (np.repeat(rows, terms), columns.reshape(-1))
    return sp.csr_matrix((weights.reshape(-1), entries), shape=shape)


def _roughness(
    first_count: int, second_count: int, first_weight: float, second_weight: float
) -> sp.csr_matrix:
    """Build roughness penalty over coefficient grid"""
    first_bend = sp.kron(second_difference(first_count), sp.eye(second_count))
    second_bend = sp.kron(sp.eye(first_count), second_difference(second_count))
    return sp.vstack(
        [np.sqrt(first_weight) * first_bend, np.sqrt(second_weight) * second_bend]
    ).tocsr()


def solve_background(
    target: np.ndarray, distances: CurveDistances, model: dict
) -> None:
    """Fit lighting lattice and glow bands"""
    height, width = target.shape
    pixel_count = distances.pixel_count

    # Lattice design over every pixel (centres on whole numbers)
    cells_x, cells_y = model["lattice"]["cells"]
    knots_x = clamped_knots(-0.5, width - 0.5, cells_x)
    knots_y = clamped_knots(-0.5, height - 0.5, cells_y)
    basis_x = basis(distances.centres[:, 0], knots_x)
    basis_y = basis(distances.centres[:, 1], knots_y)
    count_x, count_y = cells_x + SPLINE_DEGREE, cells_y + SPLINE_DEGREE
    lattice_size = count_x * count_y
    lattice_shape = (pixel_count, lattice_size)
    every_pixel = np.arange(pixel_count)
    blocks = [_tensor_design(every_pixel, basis_y, basis_x, count_x, lattice_shape)]

    # Empty penalty block for lattice columns
    penalties = [sp.csr_matrix((0, lattice_size))]

    # Band design per curve and side
    across_knots = across_knot_vector(model["band"])
    across_count = len(across_knots) - SPLINE_ORDER
    free_masks = []
    for curve, (_, arc_lengths), (pixels, along, across) in zip(
        model["curves"], distances.polylines, distances.projections
    ):
        along_count = curve["along_cells"] + SPLINE_DEGREE
        along_knots = clamped_knots(0, arc_lengths[-1], curve["along_cells"])
        band_shape = (pixel_count, along_count * across_count)

        # Pin band to zero at outer rim and tail
        is_free = np.zeros((along_count, across_count), bool)
        is_free[: along_count - BAND_PINNED, : across_count - BAND_PINNED] = True
        free_columns = np.flatnonzero(is_free.ravel())

        # Design and penalty per side, inner first
        roughness = _roughness(
            along_count, across_count, BAND_SMOOTH_ALONG, BAND_SMOOTH_ACROSS
        )
        for is_side in (across > 0, across <= 0):
            along_basis = basis(along[is_side], along_knots)
            across_basis = basis(np.abs(across[is_side]), across_knots)
            design = _tensor_design(
                pixels[is_side], along_basis, across_basis, across_count, band_shape
            )
            blocks.append(design[:, free_columns])
            penalties.append(roughness[:, free_columns])
            free_masks.append(is_free)

    # Drop stroke pixels
    design = sp.hstack(blocks).tocsr()
    is_background = (np.abs(distances.across) >= STROKE_MASK).all(axis=0)
    design, observed = design[is_background], target.ravel()[is_background]

    # Solve penalised normal equations
    penalty = sp.block_diag(penalties).tocsr()
    normal = (design.T @ design + penalty.T @ penalty).toarray()
    ridge = np.full(design.shape[1], BAND_RIDGE)
    ridge[:lattice_size] = LATTICE_RIDGE
    normal[np.diag_indices_from(normal)] += ridge * normal.trace() / len(ridge)
    solution = cho_solve(cho_factor(normal), design.T @ observed)

    # Unpack lattice then band tables
    lattice = solution[:lattice_size].reshape(count_y, count_x)
    model["lattice"]["coefficients"] = lattice
    offset = lattice_size
    for k, curve in enumerate(model["curves"]):
        for side, name in enumerate(("inner", "outer")):
            is_free = free_masks[2 * k + side]
            table = np.zeros(is_free.shape)
            table[is_free] = solution[offset : offset + is_free.sum()]
            offset += is_free.sum()
            curve[name] = table
