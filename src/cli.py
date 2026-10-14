"""Shared command line helpers"""

import logging
import sys

from config import SIZE_PRESETS


def parse_size(text: str) -> tuple[int, int]:
    """Parse size preset or WIDTHxHEIGHT"""
    size = text.lower()
    if size in SIZE_PRESETS:
        return SIZE_PRESETS[size]
    width, height = size.split("x")
    return int(width), int(height)


def configure_logging() -> None:
    """Log bare messages to stdout"""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
