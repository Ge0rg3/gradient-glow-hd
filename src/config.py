"""Paths and tuning constants"""

from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
MODEL_PATH = SRC_DIR / "data" / "gradient-glow.json"
GALLERY_TEMPLATE = SRC_DIR / "templates" / "gallery.html"
GALLERY_ASSETS = [SRC_DIR / "static" / "gallery.css", SRC_DIR / "static" / "gallery.js"]

# Original JPEGs (git-ignored) and rendered file names
ORIGINALS_DIR = SRC_DIR.parent / "originals"
ORIGINAL_NAME = "Gradient Glow {}.jpg"
RENDER_NAME = "gradient-glow-{colour}-{width}x{height}.png"

# Output sizes
SIZE_PRESETS = {
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4k": (3840, 2160),
    "5k": (5120, 2880),
    "8k": (7680, 4320),
}
SIZE_HELP = f"WIDTHxHEIGHT or {'/'.join(SIZE_PRESETS)} (default: %(default)s)"
DEFAULT_SIZE = "4k"

# Cubic splines throughout
SPLINE_DEGREE = 3
SPLINE_ORDER = SPLINE_DEGREE + 1

# Points per tensor evaluation chunk (bounds memory at 8K)
EVAL_CHUNK = 400_000

# Polyline vertex spacing in design px
FLATTEN_STEP = 0.25

# Nearest vertex search slack in design px
PROJECT_SLACK = 1.0

# Coarse grid cell for finding pixels near a curve
COARSE_CELL = 16.0

# Spare coarse cells around reach (cell rounding)
COARSE_SLACK_CELLS = 2

# Stroke reach beyond its half width, in edge sigmas
STROKE_REACH_SIGMAS = 5

# Distance given to strokes out of reach
OUT_OF_REACH = 1e6

# Dither half width in levels (hides 8-bit rounding when grain is weak)
DITHER_HALFWIDTH = 0.5

# Render defaults
GRAIN_AMOUNT = 1.0
GRAIN_SIZE = 1.0
GRAIN_SEED = 0

# Shade tints as saturation and brightness (classic matches coloured originals)
STYLES = {
    "classic": (0.78, 1.20),
    "vivid": (0.92, 1.25),
    "bright": (0.55, 1.50),
    "muted": (0.45, 1.10),
    "deep": (0.85, 0.85),
    "ash": (0.24, 0.80),
}
STYLE_BLURBS = {
    "classic": "the originals' recipe at other hues",
    "vivid": "more saturated, a touch brighter",
    "bright": "lighter and softer",
    "muted": "dusty, about half the saturation",
    "deep": "darker and richer",
    "ash": "near-greys with a hint of colour",
}

# Shade gallery
GALLERY_DIR = Path("shades")
GALLERY_PAGE = "index.html"
GALLERY_HUES = 24
THUMB_DIR = "thumbs"
THUMB_SIZE = (384, 216)
THUMB_QUALITY = 88

# Parallel shade painters (each needs about 0.7 GB at 4K)
GALLERY_WORKERS = 8

# Hue sampling step in degrees
HUE_STEP = 0.25

# Style and brightness of colour used to measure hue (mid background)
HUE_PROBE_STYLE = "classic"
HUE_PROBE_BRIGHTNESS = 0.35

# sRGB transfer curve
SRGB_LINEAR_LIMIT = 0.04045
SRGB_LINEAR_SLOPE = 12.92
SRGB_OFFSET = 0.055
SRGB_GAMMA = 2.4

# Linear sRGB to OKLab cone response
OKLAB_CONES = [
    [0.4122214708, 0.2119034982, 0.0883024619],
    [0.5363325363, 0.6806995451, 0.2817188376],
    [0.0514459929, 0.1073969566, 0.6299787005],
]
OKLAB_A = [1.9779984951, -2.4285922050, 0.4505937099]
OKLAB_B = [0.0259040371, 0.7827717662, -0.8086757660]

# Shape reference colour (grain separation needs a saturated tint)
REFERENCE_COLOUR = "blue"

# Original JPEG encoding (subsampling 0 is 4:4:4)
JPEG_QUALITY = 99
JPEG_SUBSAMPLING = 0

# Flat patch with no curves, as row and column slices
FLAT_PATCH = (slice(40, 520), slice(40, 640))

# Blur separating grain from gradient, in px
GRAIN_HIGHPASS_SIGMA = 6

# Tint estimate smoothing and pixel stride
TINT_BLUR_SIGMA = 6
TINT_STRIDE = 7

# Grain candidates tried against original, halfwidths as start, stop, step
GRAIN_SIGMAS = (0.0, 0.3, 0.6, 0.9)
GRAIN_HALFWIDTHS = (2.4, 4.41, 0.05)
CALIBRATION_SEED = 0

# Grain match tolerances for spread and kurtosis
GRAIN_SPREAD_TOLERANCE = 0.01
GRAIN_KURTOSIS_TOLERANCE = 0.02

# Ridge filter scale in px
RIDGE_SIGMA = 1.3

# Ridge follower stride and step limit
FOLLOW_STEP = 2.0
FOLLOW_MAX_STEPS = 2000

# Ridge profile sampled across and along the path
FOLLOW_OFFSETS = (-2.5, 2.5, 41)
FOLLOW_TANGENT_OFFSETS = (-4, -2, 0, 2, 4)

# Largest sideways correction per step, in px
FOLLOW_MAX_SIDESTEP = 1.0

# Stop once mean ridge strength over recent steps fades
FOLLOW_FADE_WINDOW = 15
FOLLOW_FADE_STRENGTH = 0.55

# Heading blend per step, old heading then new
FOLLOW_HEADING_KEEP = 0.7
FOLLOW_HEADING_TURN = 0.3

# Trace seeds above node, as rows and column range
SEED_ROWS = (200, 190)
SEED_ROW_COLUMNS = (1300, 1720)
SEED_ROW_STRENGTH = 1.2

# Trace seeds below node, as columns and row range
SEED_COLUMNS = (1200, 1190)
SEED_COLUMN_ROWS = (415, 1000)
SEED_COLUMN_STRENGTH = 0.9

# Smallest gap between seed peaks, in px
SEED_PEAK_GAP = 3

# Ridge strength given to seed points (above TRACE_MAX_WEIGHT cap)
SEED_STRENGTH = 9

# Rough node position and tracing stop radius
NODE_GUESS = (1316.0, 416.0)
NODE_STOP_RADIUS = 14

# Curves crossing at node
CURVE_COUNT = 4

# Traced points dropped as too faint or too near node
TRACE_MIN_STRENGTH = 1
TRACE_NODE_TRIM = 6

# Cap on ridge strength as fit weight
TRACE_MAX_WEIGHT = 4

# Curve spline knot pitch below node, in px
CURVE_CELL = 60.0

# Curve refit passes and samples for reparametrising
CURVE_FIT_PASSES = 4
CURVE_FIT_SAMPLES = 40000

# Nudge keeping reparametrised positions strictly increasing
CURVE_ORDER_NUDGE = 1e-9

# Curve extension off frame and past tail, in px
EXTEND_TOP = 170.0
EXTEND_TAIL = 60.0

# Lighting lattice pitch in px (too coarse to trace 8-bit banding)
LATTICE_CELL = 80.0

# Glow band reach either side of a curve, in px
BAND_RADIUS = 96.0

# Band knots across curve, finer near edge
BAND_ACROSS_KNOTS = [0, 6, 14, 26, 42, 66]

# Band knot pitch along curve, in px
BAND_ALONG_CELL = 24.0

# Band roughness penalty along and across (stops bands tracing banding)
BAND_SMOOTH_ALONG = 30.0
BAND_SMOOTH_ACROSS = 2.0

# Band coefficients pinned to zero at rim and tail (value and slope)
BAND_PINNED = 2

# Ridge terms keeping normal equations solvable
BAND_RIDGE = 1e-5
LATTICE_RIDGE = 1e-9

# Pixels this close to a curve count as stroke
STROKE_MASK = 2.3

# Stroke fit zone and gap to other strokes, in px
STROKE_ZONE = 2.6
STROKE_ISOLATION_SIGMAS = 3
STROKE_ISOLATION_MARGIN = 0.1

# Stroke opacity knot pitch and roughness penalty
OPACITY_CELL = 32.0
OPACITY_SMOOTH = 60.0

# Curve shift knot pitch, roughness penalty and damping
SHIFT_CELL = 30.0
SHIFT_SMOOTH = 40.0
SHIFT_DAMP = 8.0

# Largest curve shift per pass, in px
SHIFT_LIMIT = 0.4

# Finite difference step for coverage gradient, in px
SHIFT_PROBE = 0.02

# Curve resampling step when applying shift, in px
SHIFT_RESAMPLE_STEP = 2.0

# Nudge making resampling include curve end
SHIFT_RESAMPLE_NUDGE = 1e-6

# Least squares solver tolerance
LSQR_TOLERANCE = 1e-10

# Curve position passes
FIT_ITERATIONS = 6

# Starting stroke width, stroke level and edge softness
STROKE_WIDTH = 1.30
STROKE_LEVEL = 158.0
EDGE_SIGMA = 0.37

# Search grids for stroke level, width and edge softness
STROKE_LEVEL_GRID = (146.0, 181.0, 2.0)
STROKE_WIDTH_GRID = (1.1, 1.55, 0.05)
EDGE_SIGMA_GRID = (0.28, 0.50, 0.03)
SEARCH_ROUNDS = 2

# Decimals kept in model file, more for tints and knots
MODEL_DECIMALS = 4
MODEL_PRECISE_DECIMALS = 6
MODEL_PRECISE_KEYS = ("tint", "knots")

# Comparison crops as centre x, y in original px
CROP_CENTRES = {
    "node": (1315, 418),
    "upper fan": (1500, 110),
    "lower fan": (1010, 610),
    "tails": (560, 800),
    "glow": (480, 160),
}
CROP_SIZE = 150
CROP_ZOOM = 2

# Comparison output folder and crop sheet name
COMPARE_DIR = Path("compare")
CROP_SHEET_NAME = "crops-{}.png"

# Comparison render scale (2 is 4K)
COMPARE_SCALE = 2
COMPARE_SEED = 1

# Crop sheet colours and spacing, in px
SHEET_BACKGROUND = (20, 20, 20)
SHEET_TEXT = (230, 230, 230)
SHEET_GAP = 10
SHEET_LABEL_HEIGHT = 24
SHEET_LABEL_INSET = 6

# Blur radii for structure comparison, in px
STRUCTURE_BLUR = 2
WORST_ERROR_BLUR = 4

# Stroke coverage below this counts as background
STROKE_FREE_COVER = 1e-4
