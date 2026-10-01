"""Parser for raw METAR aviation weather reports.

The parser is token based. A METAR is a space-separated string of coded
groups in a fixed order: station, time, wind, visibility, weather, clouds,
temperature and dewpoint, and altimeter setting, with optional groups such
as runway visual range and trend markers along the way, and a free-text
remarks section at the end. Each group is matched against the pattern it is
expected to follow, decoded, and stored on a :class:`MetarReport`. Groups
the parser does not understand are kept in ``unparsed`` rather than dropped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from . import codes

METERS_PER_STATUTE_MILE = 1609.344
METERS_PER_FOOT = 0.3048
HPA_PER_INHG = 33.8639

_TIME_RE = re.compile(r"^(\d{2})(\d{2})(\d{2})Z$")
_WIND_RE = re.compile(r"^(VRB|\d{3})(\d{2,3})(?:G(\d{2,3}))?(KT|MPS|KMH)$")
_WIND_VAR_RE = re.compile(r"^(\d{3})V(\d{3})$")
_VIS_METERS_RE = re.compile(r"^(\d{4})(?:NE|NW|SE|SW|N|S|E|W)?$")
_VIS_SM_RE = re.compile(r"^(M)?(?:(\d+)/(\d+)|(\d+))SM$")
_VIS_FRACTION_RE = re.compile(r"^(M)?(\d+)/(\d+)SM$")
_RVR_RE = re.compile(
    r"^R(\d{2}[LRC]?)/([PM]?\d{3,4})(?:V([PM]?\d{3,4}))?(FT|M)?([UDN])?$"
)
_CLOUD_RE = re.compile(r"^(FEW|SCT|BKN|OVC|VV)(\d{3}|///)(CB|TCU)?$")
_SKY_CLEAR_RE = re.compile(r"^(SKC|CLR|NSC|NCD)(?:///|)$")
_TEMP_RE = re.compile(r"^(M?\d{2})/(M?\d{2})?$")
_QNH_RE = re.compile(r"^Q(\d{4})$")
_ALTIMETER_RE = re.compile(r"^A(\d{4})$")
_STATION_RE = re.compile(r"^[A-Z]{4}$")

_TREND_TOKENS = ("NOSIG", "TEMPO", "BECMG")


@dataclass
class Wind:
    """Surface wind group, for example ``31012G24KT``."""

    direction_deg: Optional[int]  # None when the direction is variable (VRB)
    variable: bool
    speed: float
    gust: Optional[float]
    unit: str  # KT, MPS, or KMH as reported
    var_from_deg: Optional[int] = None
    var_to_deg: Optional[int] = None


@dataclass
class RunwayVisualRange:
    """Runway visual range group, for example ``R24L/1100FT``."""

    runway: str
    low_m: float
    high_m: Optional[float]
    tendency: Optional[str]  # U (up), D (down), N (no change), or None
    raw: str


@dataclass
class WeatherGroup:
    """One present-weather group, for example ``+TSRA``."""

    raw: str
    intensity: str  # light, moderate, heavy, or in the vicinity
    descriptor: Optional[str]
    phenomena: List[str]
    description: str


@dataclass
class CloudLayer:
    """One cloud layer, for example ``SCT018`` or ``BKN040CB``."""

    amount: str  # FEW, SCT, BKN, OVC, or VV
    height_ft: Optional[int]  # None when reported as ///
    cloud_type: Optional[str] = None  # CB or TCU when reported


@dataclass
class MetarReport:
    """A decoded METAR report."""

    raw: str
    station: str
    day: int
    hour: int
    minute: int
    report_type: str = "METAR"
    auto: bool = False
    corrected: bool = False
    wind: Optional[Wind] = None
    visibility_m: Optional[float] = None
    cavok: bool = False
    rvr: List[RunwayVisualRange] = field(default_factory=list)
    weather: List[WeatherGroup] = field(default_factory=list)
    clouds: List[CloudLayer] = field(default_factory=list)
    sky_clear: bool = False
    temperature_c: Optional[int] = None
    dewpoint_c: Optional[int] = None
    qnh_hpa: Optional[float] = None
    altimeter_inhg: Optional[float] = None
    trend: Optional[str] = None
    remarks: Optional[str] = None
    unparsed: List[str] = field(default_factory=list)


def _parse_signed_temp(text):
    """Parse a temperature field where a leading M means below zero."""
    if text.startswith("M"):
        return -int(text[1:])
    return int(text)


def _parse_rvr_value(text, unit):
    """Convert an RVR value to meters, dropping any P or M prefix."""
    value = float(text.lstrip("PM"))
    if unit == "FT":
        value = value * METERS_PER_FOOT
    return round(value, 1)


def _sm_to_meters(whole, numerator, denominator, less_than):
    """Convert a statute-mile visibility (whole and/or fraction) to meters."""
    value = 0.0
    if whole is not None:
        value += int(whole)
    if numerator is not None:
        value += int(numerator) / int(denominator)
    meters = value * METERS_PER_STATUTE_MILE
    return round(meters, 1)


def parse_metar(raw):
    """Parse a raw METAR string into a :class:`MetarReport`.

    Raises ``ValueError`` when the string does not start with a station
    identifier and an observation time, the two groups every METAR has.
    """
    text = " ".join(raw.strip().split())
    tokens = text.split(" ") if text else []

    report_type = "METAR"
    if tokens and tokens[0] in ("METAR", "SPECI"):
        report_type = tokens.pop(0)

    if len(tokens) < 2 or not _STATION_RE.match(tokens[0]):
        raise ValueError("METAR must start with a 4-letter station identifier")
    station = tokens.pop(0)

    time_match = _TIME_RE.match(tokens[0]) if tokens else None
    if time_match is None:
        raise ValueError("METAR must include an observation time like 011200Z")
    day, hour, minute = (int(part) for part in time_match.groups())
    tokens.pop(0)

    report = MetarReport(
        raw=text,
        station=station,
        day=day,
        hour=hour,
        minute=minute,
        report_type=report_type,
    )

    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1

        if token == "RMK":
            report.remarks = " ".join(tokens[index:])
            break
        if token == "AUTO":
            report.auto = True
            continue
        if token == "COR":
            report.corrected = True
            continue
        if token == "CAVOK":
            report.cavok = True
            report.visibility_m = 10000.0
            continue
        if token in _TREND_TOKENS:
            if report.trend is None:
                report.trend = token
            continue

        wind_match = _WIND_RE.match(token)
        if wind_match:
            direction_text, speed_text, gust_text, unit = wind_match.groups()
            variable = direction_text == "VRB"
            report.wind = Wind(
                direction_deg=None if variable else int(direction_text),
                variable=variable,
                speed=float(speed_text),
                gust=float(gust_text) if gust_text else None,
                unit=unit,
            )
            continue

        var_match = _WIND_VAR_RE.match(token)
        if var_match and report.wind is not None:
            report.wind.var_from_deg = int(var_match.group(1))
            report.wind.var_to_deg = int(var_match.group(2))
            continue

        rvr_match = _RVR_RE.match(token)
        if rvr_match:
            runway, low_text, high_text, unit, tendency = rvr_match.groups()
            unit = unit or "M"
            report.rvr.append(
                RunwayVisualRange(
                    runway=runway,
                    low_m=_parse_rvr_value(low_text, unit),
                    high_m=(
                        _parse_rvr_value(high_text, unit) if high_text else None
                    ),
                    tendency=tendency,
                    raw=token,
                )
            )
            continue

        # Statute-mile visibility can span two tokens, as in "1 1/2SM".
        if token.isdigit() and index < len(tokens):
            fraction_match = _VIS_FRACTION_RE.match(tokens[index])
            if fraction_match:
                less_than, numerator, denominator = fraction_match.groups()
                report.visibility_m = _sm_to_meters(
                    token, numerator, denominator, less_than
                )
                index += 1
                continue

        sm_match = _VIS_SM_RE.match(token)
        if sm_match:
            less_than, numerator, denominator, whole = sm_match.groups()
            report.visibility_m = _sm_to_meters(
                whole, numerator, denominator, less_than
            )
            continue

        meters_match = _VIS_METERS_RE.match(token)
        if meters_match and report.visibility_m is None:
            report.visibility_m = float(meters_match.group(1))
            continue

        cloud_match = _CLOUD_RE.match(token)
        if cloud_match:
            amount, height_text, cloud_type = cloud_match.groups()
            report.clouds.append(
                CloudLayer(
                    amount=amount,
                    height_ft=(
                        int(height_text) * 100 if height_text != "///" else None
                    ),
                    cloud_type=cloud_type,
                )
            )
            continue

        if _SKY_CLEAR_RE.match(token):
            report.sky_clear = True
            continue

        temp_match = _TEMP_RE.match(token)
        if temp_match:
            report.temperature_c = _parse_signed_temp(temp_match.group(1))
            if temp_match.group(2):
                report.dewpoint_c = _parse_signed_temp(temp_match.group(2))
            continue

        qnh_match = _QNH_RE.match(token)
        if qnh_match:
            report.qnh_hpa = float(qnh_match.group(1))
            continue

        altimeter_match = _ALTIMETER_RE.match(token)
        if altimeter_match:
            inhg = int(altimeter_match.group(1)) / 100.0
            report.altimeter_inhg = inhg
            report.qnh_hpa = round(inhg * HPA_PER_INHG, 1)
            continue

        weather = codes.parse_weather_token(token)
        if weather is not None:
            report.weather.append(
                WeatherGroup(
                    raw=token,
                    intensity=weather["intensity"],
                    descriptor=weather["descriptor"],
                    phenomena=weather["phenomena"],
                    description=weather["description"],
                )
            )
            continue

        report.unparsed.append(token)

    return report
