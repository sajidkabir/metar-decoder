"""Tests for the weather code lookup tables and the group splitter."""

from metar_decoder import codes


def test_plain_phenomena_decode():
    result = codes.parse_weather_token("FG")
    assert result["phenomena"] == ["FG"]
    assert result["descriptor"] is None
    assert result["description"] == "fog"


def test_light_and_heavy_intensity():
    assert codes.parse_weather_token("-DZ")["description"] == "light drizzle"
    assert codes.parse_weather_token("+RA")["description"] == "heavy rain"


def test_shower_and_freezing_descriptors():
    assert codes.parse_weather_token("SHRA")["description"] == "rain shower"
    assert codes.parse_weather_token("FZRA")["description"] == "freezing rain"


def test_thunderstorm_alone_and_in_vicinity():
    assert codes.parse_weather_token("TS")["description"] == "thunderstorm"
    result = codes.parse_weather_token("VCTS")
    assert result["intensity"] == "in the vicinity"
    assert result["description"] == "thunderstorm in the vicinity"


def test_non_weather_tokens_rejected():
    assert codes.parse_weather_token("SCT018") is None
    assert codes.parse_weather_token("Q1006") is None
    assert codes.parse_weather_token("XYZW") is None
