"""Pixel positions relative to curves"""

import numpy as np

from config import BAND_RADIUS, OUT_OF_REACH
from curves import flatten, project


class CurveDistances:
    """Position of every pixel relative to every curve"""

    def __init__(self, curves: list[dict], shape: tuple[int, int]) -> None:
        """Project every pixel onto every curve"""
        # List pixel centres as x, y
        height, width = shape
        rows, columns = np.mgrid[0:height, 0:width]
        self.centres = np.c_[columns.ravel(), rows.ravel()].astype(float)
        self.pixel_count = len(self.centres)

        # Project every pixel onto each curve
        self.polylines = [flatten(curve) for curve in curves]
        self.projections = [
            project(polyline, arc_lengths, self.centres, BAND_RADIUS)
            for polyline, arc_lengths in self.polylines
        ]

        # Tabulate per curve (pixels beyond band stay out of reach)
        self.across = np.full((len(curves), self.pixel_count), OUT_OF_REACH)
        self.along = np.zeros((len(curves), self.pixel_count))
        for k, (pixels, along, across) in enumerate(self.projections):
            self.across[k, pixels] = across
            self.along[k, pixels] = along
