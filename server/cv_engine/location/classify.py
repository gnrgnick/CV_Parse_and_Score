"""Location pre-filter: maps a Candidate's extracted location fields to a band + score."""
from __future__ import annotations

from cv_engine.models import Candidate, LocationBand

TARGET_INWARD: set[str] = {"W", "NW", "HA", "UB", "SL", "SW"}

# Small curated list of area keywords that flag REVIEW when the postcode is missing.
# Keep this tight — REVIEW exists to rescue candidates with an obvious target-area location
# that didn't make it into the postcode field, not to approximate a geographic distance model.
_TARGET_AREA_KEYWORDS: tuple[str, ...] = (
    "ealing", "harrow", "brent", "slough", "hillingdon", "wembley",
    "uxbridge", "ruislip", "northolt", "greenford", "southall",
    "acton", "hammersmith", "kensington", "chelsea",
)


def mentions_target_area(freetext: str) -> bool:
    lowered = freetext.lower()
    return any(keyword in lowered for keyword in _TARGET_AREA_KEYWORDS)


def classify(candidate: Candidate) -> tuple[LocationBand, int]:
    inward = candidate.postcode_inward
    freetext = candidate.location_freetext

    if inward:
        return ("PASS", 20) if inward.upper() in TARGET_INWARD else ("FAIL", 0)
    if freetext and mentions_target_area(freetext):
        return ("REVIEW", 10)
    return ("NO_DATA", 5)
