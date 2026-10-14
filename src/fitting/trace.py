"""Curve tracing along bright ridges"""

import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import make_lsq_spline
from scipy.signal import find_peaks
from scipy.spatial import cKDTree

from config import (
    CURVE_CELL,
    CURVE_COUNT,
    CURVE_FIT_PASSES,
    CURVE_FIT_SAMPLES,
    CURVE_ORDER_NUDGE,
    FOLLOW_FADE_STRENGTH,
    FOLLOW_FADE_WINDOW,
    FOLLOW_HEADING_KEEP,
    FOLLOW_HEADING_TURN,
    FOLLOW_MAX_SIDESTEP,
    FOLLOW_MAX_STEPS,
    FOLLOW_OFFSETS,
    FOLLOW_STEP,
    FOLLOW_TANGENT_OFFSETS,
    NODE_GUESS,
    NODE_STOP_RADIUS,
    RIDGE_SIGMA,
    SEED_COLUMN_ROWS,
    SEED_COLUMN_STRENGTH,
    SEED_COLUMNS,
    SEED_PEAK_GAP,
    SEED_ROW_COLUMNS,
    SEED_ROW_STRENGTH,
    SEED_ROWS,
    SEED_STRENGTH,
    SPLINE_DEGREE,
    SPLINE_ORDER,
    TRACE_MIN_STRENGTH,
    TRACE_NODE_TRIM,
)


def _ridge_strength(brightness: np.ndarray) -> np.ndarray:
    """Measure bright ridge strength per pixel"""
    # Second derivatives of smoothed brightness
    bend_xx = ndi.gaussian_filter(brightness, RIDGE_SIGMA, order=(0, 2))
    bend_yy = ndi.gaussian_filter(brightness, RIDGE_SIGMA, order=(2, 0))
    bend_xy = ndi.gaussian_filter(brightness, RIDGE_SIGMA, order=(1, 1))

    # Negate smaller eigenvalue (bright line bends down across itself)
    smaller = (bend_xx + bend_yy) / 2 - np.hypot((bend_xx - bend_yy) / 2, bend_xy)
    return np.clip(-smaller, 0, None)


def _follow(
    ridge_spline: np.ndarray,
    shape: tuple[int, int],
    start: tuple[float, float],
    heading: np.ndarray,
    stops_at_node: bool,
) -> np.ndarray:
    """Follow ridge, return x, y and strength"""
    position = np.array(start, float)
    heading = heading / np.linalg.norm(heading)
    offsets = np.linspace(*FOLLOW_OFFSETS)
    spacing = offsets[1] - offsets[0]
    traced, strengths = [], []
    for _ in range(FOLLOW_MAX_STEPS):
        # Step along heading
        ahead = position + heading * FOLLOW_STEP
        normal = np.array([-heading[1], heading[0]])

        # Average ridge profile across path
        profile = np.zeros(len(offsets))
        for tangent_offset in FOLLOW_TANGENT_OFFSETS:
            samples = (
                ahead[None] + heading * tangent_offset + offsets[:, None] * normal[None]
            )
            profile += ndi.map_coordinates(
                ridge_spline,
                [samples[:, 1], samples[:, 0]],
                order=SPLINE_DEGREE,
                mode="nearest",
                prefilter=False,
            )
        profile /= len(FOLLOW_TANGENT_OFFSETS)

        # Re-centre on ridge peak (parabola through three samples)
        peak = int(np.argmax(profile))
        sidestep = offsets[peak]
        if 0 < peak < len(offsets) - 1:
            before, at_peak, after = profile[peak - 1 : peak + 2]
            bend = before - 2 * at_peak + after
            sidestep += 0.5 * (before - after) / bend * spacing
        ahead = ahead + normal * np.clip(
            sidestep, -FOLLOW_MAX_SIDESTEP, FOLLOW_MAX_SIDESTEP
        )

        # Stop at frame edge or node
        is_in_frame = 0 <= ahead[0] < shape[1] - 1 and 0 <= ahead[1] < shape[0] - 1
        is_at_node = (
            stops_at_node and np.linalg.norm(ahead - NODE_GUESS) < NODE_STOP_RADIUS
        )
        if not is_in_frame or is_at_node:
            break

        # Stop once ridge fades
        strengths.append(profile.max())
        recent = strengths[-FOLLOW_FADE_WINDOW:]
        if (
            len(strengths) > FOLLOW_FADE_WINDOW
            and np.mean(recent) < FOLLOW_FADE_STRENGTH
        ):
            break

        # Turn heading towards last step
        last_step = (ahead - position) / np.linalg.norm(ahead - position)
        heading = FOLLOW_HEADING_KEEP * heading + FOLLOW_HEADING_TURN * last_step
        heading /= np.linalg.norm(heading)

        # Advance and record point
        position = ahead
        traced.append((ahead[0], ahead[1], profile.max()))
    return np.array(traced)


def trace_curves(brightness: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    """Trace each curve, raises on wrong seed count"""
    # Measure ridge strength (prefiltered once for cubic sampling)
    ridge = _ridge_strength(brightness)
    ridge_spline = ndi.spline_filter(ridge, order=SPLINE_DEGREE)
    shape = brightness.shape

    # Seed above node on two rows
    first, last = SEED_ROW_COLUMNS
    row_seeds = [
        first
        + find_peaks(
            ridge[row, first:last], height=SEED_ROW_STRENGTH, distance=SEED_PEAK_GAP
        )[0]
        for row in SEED_ROWS
    ]

    # Seed below node on two columns
    top, bottom = SEED_COLUMN_ROWS
    column_seeds = [
        top
        + find_peaks(
            ridge[top:bottom, column],
            height=SEED_COLUMN_STRENGTH,
            distance=SEED_PEAK_GAP,
        )[0]
        for column in SEED_COLUMNS
    ]

    # Check seed count on every line
    if any(len(seeds) != CURVE_COUNT for seeds in row_seeds + column_seeds):
        raise ValueError(f"expected {CURVE_COUNT} curves at every trace seed line")

    traces = []
    for k in range(CURVE_COUNT):
        # Trace upper branch both ways from seed row
        start = (row_seeds[0][k], float(SEED_ROWS[0]))
        upward = np.array(
            [row_seeds[1][k] - row_seeds[0][k], SEED_ROWS[1] - SEED_ROWS[0]], float
        )
        to_top = _follow(ridge_spline, shape, start, upward, False)
        to_node = _follow(ridge_spline, shape, start, -upward, True)
        upper = np.vstack([to_top[::-1], [[*start, SEED_STRENGTH]], to_node])

        # Trace lower branch (steepest above node is steepest below)
        mirrored = CURVE_COUNT - 1 - k
        start = (float(SEED_COLUMNS[0]), float(column_seeds[0][mirrored]))
        leftward = np.array(
            [
                SEED_COLUMNS[1] - SEED_COLUMNS[0],
                column_seeds[1][mirrored] - column_seeds[0][mirrored],
            ],
            float,
        )
        to_node = _follow(ridge_spline, shape, start, -leftward, True)
        to_tail = _follow(ridge_spline, shape, start, leftward, False)
        lower = np.vstack([to_node[::-1], [[*start, SEED_STRENGTH]], to_tail])

        # Drop faint points and points beside node
        upper = upper[upper[:, 2] >= TRACE_MIN_STRENGTH][:-TRACE_NODE_TRIM]
        lower = lower[lower[:, 2] >= TRACE_MIN_STRENGTH][TRACE_NODE_TRIM:]
        traces.append((upper, lower))
    return traces


def fit_curve(
    points: np.ndarray, weights: np.ndarray, node_index: int
) -> tuple[np.ndarray, np.ndarray, float]:
    """Fit arc-length spline through ordered points"""
    # Start from chord lengths
    positions = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    for _ in range(CURVE_FIT_PASSES):
        # Place node midway between neighbouring points
        length = positions[-1]
        node_position = 0.5 * (positions[node_index - 1] + positions[node_index])

        # Place knots (two pieces above node, even pitch below)
        cells_below = int(round((length - node_position) / CURVE_CELL))
        below = np.linspace(node_position, length, cells_below + 1)[1:-1]
        interior = np.r_[node_position / 2, node_position, below]
        knots = np.r_[[0.0] * SPLINE_ORDER, interior, [length] * SPLINE_ORDER]

        # Fit weighted spline
        spline = make_lsq_spline(positions, points, knots, k=SPLINE_DEGREE, w=weights)

        # Reparametrise points by closest spline position
        dense = np.linspace(0, length, CURVE_FIT_SAMPLES)
        closest = cKDTree(spline(dense)).query(points)[1]
        positions = dense[closest] + np.arange(len(points)) * CURVE_ORDER_NUDGE
    return spline.t, spline.c, node_position
