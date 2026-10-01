"""Parser tests, run against real-world style METAR reports."""

import pytest

from metar_decoder import parse_metar

DHAKA = "VGHS 011200Z 18008KT 4000 HZ SCT018 BKN100 31/27 Q1006 NOSIG"
JFK = "KJFK 011751Z 31012G24KT 10SM FEW045 SCT250 24/13 A2992 RMK AO2"
THUNDERSTORM = (
    "VHHH 011230Z 24015G30KT 2500 +TSRA SCT015CB BKN040 26/24 Q1002 TEMPO"
)
FOG = "EGLL 010550Z 05003KT 0300 FG VV001 M01/M01 Q1030 NOSIG"
CAVOK_REPORT = "OMDB 011200Z 32006KT CAVOK 38/24 Q1009 NOSIG"
VARIABLE_WIND = "EDDM 011220Z VRB02KT 9999 FEW040 12/05 Q1018 NOSIG"
VARYING_DIRECTION = "EHAM 011225Z 27008KT 240V300 9999 SCT045 15/08 Q1020 NOSIG"
RVR_REPORT = "EGLL 011250Z 27010KT 1200 R24L/1100FT BR BKN002 10/10 Q0995 NOSIG"


def test_dhaka_station_and_time():
    report = parse_metar(DHAKA)
    assert report.station == "VGHS"
    assert report.day == 1
    assert report.hour == 12
    assert report.minute == 0


def test_dhaka_wind():
    wind = parse_metar(DHAKA).wind
    assert wind.direction_deg == 180
    assert wind.speed == 8
    assert wind.gust is None
    assert wind.unit == "KT"
    assert wind.variable is False


def test_dhaka_visibility_and_weather():
    report = parse_metar(DHAKA)
    assert report.visibility_m == 4000
    assert len(report.weather) == 1
    assert report.weather[0].phenomena == ["HZ"]
    assert report.weather[0].description == "haze"


def test_dhaka_clouds_temperature_qnh_trend():
    report = parse_metar(DHAKA)
    assert [(c.amount, c.height_ft) for c in report.clouds] == [
        ("SCT", 1800),
        ("BKN", 10000),
    ]
    assert report.temperature_c == 31
    assert report.dewpoint_c == 27
    assert report.qnh_hpa == 1006
    assert report.trend == "NOSIG"


def test_jfk_gusts():
    wind = parse_metar(JFK).wind
    assert wind.direction_deg == 310
    assert wind.speed == 12
    assert wind.gust == 24


def test_jfk_statute_mile_visibility_converted_to_meters():
    report = parse_metar(JFK)
    assert report.visibility_m == pytest.approx(16093.4, abs=0.5)


def test_jfk_altimeter_inhg_and_hpa_conversion():
    report = parse_metar(JFK)
    assert report.altimeter_inhg == pytest.approx(29.92)
    assert report.qnh_hpa == pytest.approx(1013.2, abs=0.5)


def test_jfk_remarks_kept_raw():
    report = parse_metar(JFK)
    assert report.remarks == "AO2"


def test_thunderstorm_with_rain_and_cb():
    report = parse_metar(THUNDERSTORM)
    assert len(report.weather) == 1
    group = report.weather[0]
    assert group.intensity == "heavy"
    assert group.descriptor == "TS"
    assert group.phenomena == ["RA"]
    assert group.description == "heavy thunderstorm with rain"
    cb_layers = [c for c in report.clouds if c.cloud_type == "CB"]
    assert len(cb_layers) == 1
    assert cb_layers[0].height_ft == 1500
    assert report.trend == "TEMPO"


def test_fog_and_vertical_visibility():
    report = parse_metar(FOG)
    assert report.visibility_m == 300
    assert report.weather[0].phenomena == ["FG"]
    assert report.weather[0].description == "fog"
    assert report.clouds[0].amount == "VV"
    assert report.clouds[0].height_ft == 100


def test_negative_temperatures():
    report = parse_metar(FOG)
    assert report.temperature_c == -1
    assert report.dewpoint_c == -1


def test_cavok_expansion():
    report = parse_metar(CAVOK_REPORT)
    assert report.cavok is True
    assert report.visibility_m >= 10000
    assert report.clouds == []
    assert report.weather == []


def test_variable_wind():
    wind = parse_metar(VARIABLE_WIND).wind
    assert wind.variable is True
    assert wind.direction_deg is None
    assert wind.speed == 2


def test_wind_direction_variation_range():
    wind = parse_metar(VARYING_DIRECTION).wind
    assert wind.direction_deg == 270
    assert wind.var_from_deg == 240
    assert wind.var_to_deg == 300


def test_runway_visual_range():
    report = parse_metar(RVR_REPORT)
    assert len(report.rvr) == 1
    rvr = report.rvr[0]
    assert rvr.runway == "24L"
    assert rvr.low_m == pytest.approx(335.3, abs=0.5)


def test_fractional_statute_mile_visibility():
    report = parse_metar(
        "KJFK 011751Z 31012KT 1 1/2SM BR FEW010 24/23 A2992"
    )
    assert report.visibility_m == pytest.approx(2414.0, abs=0.5)


def test_missing_station_or_time_rejected():
    with pytest.raises(ValueError):
        parse_metar("18008KT 4000 HZ")
