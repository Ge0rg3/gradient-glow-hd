"""Wallpapers applied to KDE Plasma activities"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Desktop script run inside plasmashell
ASSIGN_SCRIPT = Path(__file__).resolve().parent / "assign_wallpapers.js"

# Plasma scripting call
PLASMA_EVALUATE = [
    "qdbus-qt6",
    "org.kde.plasmashell",
    "/PlasmaShell",
    "org.kde.PlasmaShell.evaluateScript",
]


def main() -> None:
    """Set one image per activity"""
    # Parse arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "assignments",
        nargs="+",
        metavar="ACTIVITY=IMAGE",
        help="activity name and the image file it gets, "
        "e.g. Default=gradient-glow-blue-3840x2160.png",
    )
    args = parser.parse_args()

    # Log bare messages to stdout
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    # Resolve each image to an absolute file URL
    image_by_activity = {}
    for assignment in args.assignments:
        activity, separator, image = assignment.partition("=")
        if not separator:
            parser.error(f"expected ACTIVITY=IMAGE, got {assignment}")
        path = Path(image).expanduser().resolve()
        if not path.is_file():
            parser.error(f"no image at {path}")
        image_by_activity[activity] = f"file://{path}"

    # Run script inside plasmashell (stderr left on terminal for Plasma errors)
    plan = f"const wallpaperByActivity = {json.dumps(image_by_activity)};\n"
    script = plan + ASSIGN_SCRIPT.read_text()
    report = subprocess.run(
        [*PLASMA_EVALUATE, script], check=True, stdout=subprocess.PIPE, text=True
    ).stdout.strip()

    # Log script report
    logger.info(report)


if __name__ == "__main__":
    main()
