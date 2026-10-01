"""Tests for the plain-English rendering and the command-line interface."""

import json

from metar_decoder import human_readable, parse_metar
from metar_decoder.cli import main

DHAKA = "VGHS 011200Z 18008KT 4000 HZ SCT018 BKN100 31/27 Q1006 NOSIG"
JFK = "KJFK 011751Z 31012G24KT 10SM FEW045 SCT250 24/13 A2992 RMK AO2"


def test_human_readable_dhaka_key_phrases():
    text = human_readable(parse_metar(DHAKA))
    assert "VGHS" in text
    assert "from 180 degrees at 8 knots" in text
    assert "4,000 m" in text
    assert "haze" in text
    assert "scattered at 1,800 ft" in text
    assert "broken at 10,000 ft" in text
    assert "31 C" in text
    assert "QNH 1006 hPa" in text
    assert "NOSIG" in text


def test_human_readable_jfk_gusts_and_inches():
    text = human_readable(parse_metar(JFK))
    assert "gusting to 24 knots" in text
    assert "10 km or more" in text
    assert "29.92 inHg" in text
    assert "AO2" in text


def test_cli_decode_prints_summary(capsys):
    assert main(["decode", DHAKA]) == 0
    out = capsys.readouterr().out
    assert "Wind: from 180 degrees at 8 knots" in out
    assert "Conditions: haze" in out


def test_cli_parse_prints_json(capsys):
    assert main(["parse", DHAKA]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["station"] == "VGHS"
    assert data["wind"]["speed"] == 8
    assert data["clouds"][0]["amount"] == "SCT"
    assert data["qnh_hpa"] == 1006
