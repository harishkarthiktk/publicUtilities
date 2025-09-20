# config.py
"""
Thresholds and mapping factors for auto-correction.
Tune these values based on your image set.
All thresholds are in 0-255 intensity space unless noted.
"""

# Brightness (grayscale mean)
BRIGHTNESS = {
    "dark_thresh": 80,        # mean < dark_thresh => consider image dark
    "bright_thresh": 180,     # mean > bright_thresh => consider image bright
    "dark_factor": 1.25,      # multiply brightness when dark
    "bright_factor": 0.85,    # multiply brightness when too bright
    "neutral_factor": 1.0,
}

# Contrast (stddev of grayscale)
CONTRAST = {
    "low_thresh": 35,         # stddev < low_thresh => low contrast
    "high_thresh": 110,       # stddev > high_thresh => high contrast (maybe reduce)
    "low_factor": 1.4,
    "high_factor": 0.95,
    "neutral_factor": 1.0,
}

# Color / Saturation (HSV 'S' channel)
COLOR = {
    "low_saturation_thresh": 60,  # mean S < this => undersaturated
    "boost_factor": 1.3,
    "neutral_factor": 1.0,
}

# Sharpness (variance of laplacian or gradient)
SHARPNESS = {
    "blur_thresh": 100.0,     # metric < blur_thresh => blurry
    "boost_factor": 1.5,
    "neutral_factor": 1.0,
}

# General safety caps (don't go insane)
SAFETY = {
    "max_enhance": 3.0,       # maximum enhancement factor for any single enhancer
    "min_enhance": 0.5,       # minimum enhancement factor
}
