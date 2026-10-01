"""Plain-English rendering of a decoded METAR report."""

from __future__ import annotations

from . import codes

_UNIT_WORDS = {
    "KT": "knots",
    "MPS": "m/s",
    "KMH": "km/h",
}

_TREND_TEXT = {
    "NOSIG": "no significant change expected",
    "TEMPO": "temporary fluctuations expected",
    "BECMG": "a gradual change expected",
}


def _format_number(value):
    """Format a speed or distance without a trailing .0 when it is whole."""
    if float(value) == int(value):
        return "{:,}".format(int(value))
    return "{:,.1f}".format(value)


def _format_pressure(value):
    """Format a pressure value the way it is written in reports (no commas)."""
    if float(value) == int(value):
        return str(int(value))
    return "{:.1f}".format(value)


def _wind_text(wind):
    if wind is None:
        return "not reported"
    unit = _UNIT_WORDS.get(wind.unit, wind.unit)
    speed = _format_number(wind.speed)
    if wind.speed == 0:
        text = "calm"
    elif wind.variable:
        text = "variable at {} {}".format(speed, unit)
    else:
        text = "from {} degrees at {} {}".format(wind.direction_deg, speed, unit)
    if wind.gust:
        text += ", gusting to {} {}".format(_format_number(wind.gust), unit)
    if wind.var_from_deg is not None and wind.var_to_deg is not None:
        text += ", varying between {} and {} degrees".format(
            wind.var_from_deg, wind.var_to_deg
        )
    return text


def _visibility_text(report):
    if report.cavok:
        return "10 km or more (CAVOK: no significant cloud or weather)"
    if report.visibility_m is None:
        return "not reported"
    if report.visibility_m == 0:
        return "less than 50 m"
    if report.visibility_m >= 9999:
        return "10 km or more"
    return "{} m".format(_format_number(report.visibility_m))


def _cloud_text(report):
    if report.cavok:
        return "none significant (CAVOK)"
    if not report.clouds:
        if report.sky_clear:
            return "clear sky"
        return "none reported"
    parts = []
    for layer in report.clouds:
        amount_text = codes.CLOUD_AMOUNTS.get(layer.amount, layer.amount)
        if layer.amount == "VV":
            if layer.height_ft is None:
                parts.append("sky obscured, vertical visibility not reported")
            else:
                parts.append(
                    "sky obscured, vertical visibility {} ft".format(
                        _format_number(layer.height_ft)
                    )
                )
            continue
        part = amount_text
        if layer.cloud_type:
            part += " " + codes.CLOUD_TYPES.get(layer.cloud_type, layer.cloud_type)
        if layer.height_ft is None:
            part += ", height not reported"
        else:
            part += " at {} ft".format(_format_number(layer.height_ft))
        parts.append(part)
    return "; ".join(parts)


def human_readable(report):
    """Render a :class:`MetarReport` as a plain-English summary."""
    lines = []
    header = "{} for {}, observed on day {:02d} at {:02d}:{:02d} UTC".format(
        report.report_type, report.station, report.day, report.hour, report.minute
    )
    if report.auto:
        header += " (automated report)"
    lines.append(header)
    lines.append("Wind: " + _wind_text(report.wind))
    lines.append("Visibility: " + _visibility_text(report))
    for rvr in report.rvr:
        text = "Runway visual range, runway {}: {} m".format(
            rvr.runway, _format_number(rvr.low_m)
        )
        if rvr.high_m is not None:
            text += " varying to {} m".format(_format_number(rvr.high_m))
        lines.append(text)
    if report.weather:
        conditions = "; ".join(group.description for group in report.weather)
        lines.append("Conditions: " + conditions)
    lines.append("Clouds: " + _cloud_text(report))
    if report.temperature_c is not None:
        text = "Temperature: {} C".format(report.temperature_c)
        if report.dewpoint_c is not None:
            text += ", dewpoint: {} C".format(report.dewpoint_c)
        lines.append(text)
    if report.qnh_hpa is not None:
        if report.altimeter_inhg is not None:
            lines.append(
                "Pressure: {:.2f} inHg (QNH {} hPa)".format(
                    report.altimeter_inhg, _format_pressure(report.qnh_hpa)
                )
            )
        else:
            lines.append(
                "Pressure: QNH {} hPa".format(_format_pressure(report.qnh_hpa))
            )
    if report.trend is not None:
        lines.append(
            "Trend: {} ({})".format(
                report.trend, _TREND_TEXT.get(report.trend, report.trend)
            )
        )
    if report.remarks:
        lines.append("Remarks: " + report.remarks)
    return "\n".join(lines)
