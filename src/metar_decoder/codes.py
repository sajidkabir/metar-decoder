"""Lookup tables and decoding helpers for METAR code groups.

METAR reports compress the weather into two-letter codes. This module holds
the plain-English tables for those codes and a helper that splits one raw
weather group (for example ``+TSRA`` or ``-SHRA``) into its intensity,
descriptor, and phenomena parts.
"""

from __future__ import annotations

# Intensity prefixes that can lead a weather group.
INTENSITIES = {
    "-": "light",
    "+": "heavy",
    "": "moderate",
    "VC": "in the vicinity",
}

# Descriptors qualify the phenomena that follow them.
DESCRIPTORS = {
    "MI": "shallow",
    "BC": "patches of",
    "DR": "low drifting",
    "BL": "blowing",
    "SH": "shower",
    "TS": "thunderstorm",
    "FZ": "freezing",
    "PR": "partial",
}

# Precipitation and obscuration phenomena.
PHENOMENA = {
    "DZ": "drizzle",
    "RA": "rain",
    "SN": "snow",
    "SG": "snow grains",
    "IC": "ice crystals",
    "PL": "ice pellets",
    "GR": "hail",
    "GS": "small hail",
    "UP": "unknown precipitation",
    "BR": "mist",
    "FG": "fog",
    "FU": "smoke",
    "VA": "volcanic ash",
    "DU": "widespread dust",
    "SA": "sand",
    "HZ": "haze",
    "PO": "dust whirls",
    "SQ": "squalls",
    "FC": "funnel cloud",
    "SS": "sandstorm",
    "DS": "duststorm",
}

# Cloud amount codes, as reported in cloud groups and sky condition groups.
CLOUD_AMOUNTS = {
    "FEW": "few",
    "SCT": "scattered",
    "BKN": "broken",
    "OVC": "overcast",
    "VV": "vertical visibility",
    "SKC": "sky clear",
    "CLR": "clear",
    "NSC": "no significant cloud",
    "NCD": "no cloud detected",
}

# Significant cloud types that can be appended to a cloud group.
CLOUD_TYPES = {
    "CB": "cumulonimbus",
    "TCU": "towering cumulus",
}


def _join_words(words):
    """Join one or more words the way a sentence list would read."""
    if len(words) <= 2:
        return " and ".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]


def describe_weather(intensity, descriptor, phenomena):
    """Build a plain-English description from decoded weather parts.

    ``intensity`` is one of the values from :data:`INTENSITIES`,
    ``descriptor`` is a code from :data:`DESCRIPTORS` or ``None``, and
    ``phenomena`` is a list of codes from :data:`PHENOMENA`.
    """
    names = [PHENOMENA[code] for code in phenomena]
    phenomena_text = _join_words(names) if names else ""

    if descriptor == "TS":
        base = "thunderstorm"
        if phenomena_text:
            base = base + " with " + phenomena_text
    elif descriptor == "SH":
        base = (phenomena_text + " shower") if phenomena_text else "showers"
    elif descriptor is not None:
        base = DESCRIPTORS[descriptor]
        if phenomena_text:
            base = base + " " + phenomena_text
    else:
        base = phenomena_text

    if intensity in ("light", "heavy"):
        base = intensity + " " + base
    elif intensity == "in the vicinity":
        base = base + " in the vicinity"
    return base


def parse_weather_token(token):
    """Split a raw weather group into its parts, or return ``None``.

    Returns a dict with ``intensity``, ``descriptor``, ``phenomena``, and
    ``description`` keys when the token is a valid weather group, and
    ``None`` when it is not (so the parser can try other group types).
    """
    body = token
    intensity = "moderate"
    if body.startswith("VC"):
        intensity = "in the vicinity"
        body = body[2:]
    elif body[:1] in ("-", "+"):
        intensity = INTENSITIES[body[0]]
        body = body[1:]

    if not body or len(body) % 2 != 0:
        return None

    descriptor = None
    rest = body
    if len(rest) > 2 and rest[:2] in DESCRIPTORS:
        descriptor = rest[:2]
        rest = rest[2:]
    elif rest in DESCRIPTORS and rest not in PHENOMENA:
        descriptor = rest
        rest = ""

    phenomena = []
    while rest:
        code = rest[:2]
        if code not in PHENOMENA:
            return None
        phenomena.append(code)
        rest = rest[2:]

    if descriptor is None and not phenomena:
        return None

    return {
        "intensity": intensity,
        "descriptor": descriptor,
        "phenomena": phenomena,
        "description": describe_weather(intensity, descriptor, phenomena),
    }
