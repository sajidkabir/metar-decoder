# metar-decoder

[![CI](https://github.com/sajidkabir/metar-decoder/actions/workflows/ci.yml/badge.svg)](https://github.com/sajidkabir/metar-decoder/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

A METAR decoder written in pure Python. It takes a raw aviation weather
report, the kind pilots and dispatchers read before every flight, and turns
it into structured data and a plain-English summary. No dependencies, no
network calls: just the standard library and the WMO code tables.

```text
VGHS 011200Z 18008KT 4000 HZ SCT018 BKN100 31/27 Q1006 NOSIG
```

becomes

```text
METAR for VGHS, observed on day 01 at 12:00 UTC
Wind: from 180 degrees at 8 knots
Visibility: 4,000 m
Conditions: haze
Clouds: scattered at 1,800 ft; broken at 10,000 ft
Temperature: 31 C, dewpoint: 27 C
Pressure: QNH 1006 hPa
Trend: NOSIG (no significant change expected)
```

## Features

- **Full core report**: station identifier, observation time, AUTO flag,
  and every standard group of a METAR or SPECI report.
- **Wind**: direction, speed, and gusts in knots, m/s, or km/h, including
  VRB variable wind and the variable direction range (for example
  `240V300`).
- **Visibility**: meters, or statute miles converted to meters (including
  fractions like `1 1/2SM`), plus CAVOK handling.
- **Runway visual range**: runway, value, and tendency, with feet
  converted to meters.
- **Weather phenomena**: intensity, descriptors, and phenomena decoded
  from the code tables, so `+TSRA` reads as "heavy thunderstorm with
  rain" and `FZRA` as "freezing rain".
- **Clouds**: layer amount, height in feet, and CB/TCU type, including
  vertical visibility for an obscured sky.
- **Temperature and pressure**: negative temperatures (`M01` is minus 1),
  QNH in hPa, and US altimeter settings in inHg converted to hPa.
- **Trend and remarks**: NOSIG, TEMPO, and BECMG markers flagged, and the
  remarks section preserved raw.
- **Two outputs**: a structured `MetarReport` dataclass (JSON ready) and
  a plain-English summary. Groups the parser cannot decode are kept in an
  `unparsed` list, never silently dropped.

## Installation

Requires Python 3.10 or newer. No third-party dependencies.

```bash
git clone https://github.com/sajidkabir/metar-decoder.git
cd metar-decoder
pip install -e .
```

For development (adds the test runner):

```bash
pip install -e . pytest
pytest -q
```

## Quickstart

### Command line

Decode a report into plain English:

```bash
metar decode "VGHS 011200Z 18008KT 4000 HZ SCT018 BKN100 31/27 Q1006 NOSIG"
```

```text
METAR for VGHS, observed on day 01 at 12:00 UTC
Wind: from 180 degrees at 8 knots
Visibility: 4,000 m
Conditions: haze
Clouds: scattered at 1,800 ft; broken at 10,000 ft
Temperature: 31 C, dewpoint: 27 C
Pressure: QNH 1006 hPa
Trend: NOSIG (no significant change expected)
```

A US report with gusts and an inches altimeter setting:

```bash
metar decode "KJFK 011751Z 31012G24KT 10SM FEW045 SCT250 24/13 A2992 RMK AO2"
```

```text
METAR for KJFK, observed on day 01 at 17:51 UTC
Wind: from 310 degrees at 12 knots, gusting to 24 knots
Visibility: 10 km or more
Clouds: few at 4,500 ft; scattered at 25,000 ft
Temperature: 24 C, dewpoint: 13 C
Pressure: 29.92 inHg (QNH 1013.2 hPa)
Remarks: AO2
```

Or get the structured report as JSON:

```bash
metar parse "VGHS 011200Z 18008KT 4000 HZ SCT018 BKN100 31/27 Q1006 NOSIG"
```

### Python API

```python
from metar_decoder import human_readable, parse_metar

report = parse_metar(
    "VHHH 011230Z 24015G30KT 2500 +TSRA SCT015CB BKN040 26/24 Q1002 TEMPO"
)

report.wind.speed              # 15.0
report.wind.gust               # 30.0
report.weather[0].description  # "heavy thunderstorm with rain"
report.clouds[0].cloud_type    # "CB"
report.clouds[0].height_ft     # 1500
report.qnh_hpa                 # 1002.0
report.trend                   # "TEMPO"

print(human_readable(report))
```

## How it works

| Module | Responsibility |
| --- | --- |
| `parser.py` | Token-based parser and the report dataclasses |
| `codes.py` | Weather and cloud code tables, weather group splitter |
| `report.py` | Plain-English rendering of a decoded report |
| `cli.py` | Command-line interface (`decode`, `parse`) |

The parser walks the report group by group in the order the METAR format
defines them. Each group is matched against the pattern it is expected to
follow, decoded, and stored in a typed field. A few conventions worth
knowing:

- Statute miles convert at 1 SM = 1609.344 m, inches of mercury at
  1 inHg = 33.8639 hPa.
- Cloud heights are reported in hundreds of feet: `SCT018` is a scattered
  layer at 1,800 ft.
- A leading M in a temperature means below zero: `M01/M01` is minus 1 C
  with a dewpoint of minus 1 C.
- CAVOK replaces the visibility, weather, and cloud groups entirely: it
  means visibility of 10 km or more and no significant cloud or weather.

## Validation and sanity checks

The test suite (26 tests) checks the decoding, field by field, against
eight real-world style reports from Dhaka, New York, Hong Kong, London,
Amsterdam, Munich, and Dubai:

- Every field of the Dhaka report: wind, visibility, haze, both cloud
  layers, temperature and dewpoint, QNH, and the NOSIG trend.
- Gusts parsed separately from the sustained wind speed.
- Statute-mile visibility converted to meters, whole and fractional.
- An inHg altimeter setting kept in inches and also converted to hPa.
- Heavy thunderstorm with rain decoded from intensity, descriptor, and
  phenomenon, with the cumulonimbus layer flagged.
- Fog with an obscured sky: vertical visibility instead of a cloud layer.
- Negative temperatures from M-prefixed fields.
- CAVOK expanded to 10 km or more with no cloud and no weather groups.
- VRB wind with no direction, and a variable direction range attached to
  the wind group.
- The plain-English output contains the phrases a reader would look for,
  and the CLI emits valid JSON with the expected values.

## Honest limitations

- METAR and SPECI only. TAF forecasts are a different format and are not
  decoded yet.
- Trend groups are flagged (NOSIG, TEMPO, BECMG) but the forecast groups
  that can follow a TEMPO or BECMG marker are not decoded.
- Remarks are preserved raw. Coded remarks such as sea-level pressure or
  hourly temperature groups are not expanded.
- Runway visual range values with P (more than) or M (less than)
  prefixes are stored at their numeric value; the qualifier is kept only
  in the raw group text.
- Wind shear groups and runway state groups are not modeled; they land
  in the report's `unparsed` list.
- There is no station database: the station is reported by its ICAO code,
  not expanded to a station name.

These are deliberate. Each one is a clean extension point, listed below.

## Roadmap and room for exploration

Ideas are welcome. Roughly in order of expected value:

- **TAF decoding**: the forecast format shares most groups with METAR, so
  the parser core can grow a second entry point, including FM, BECMG,
  TEMPO, and probability groups decoded in full.
- **Flight category classification**: derive VFR, MVFR, IFR, and LIFR
  categories from visibility and ceiling, the way briefing tools do.
- **Remarks decoding**: expand the common coded remarks (automated
  station type, sea-level pressure, precise temperature groups).
- **Trend group decoding**: full decoding of the forecast groups that
  follow TEMPO and BECMG markers.
- **Station metadata**: an optional lookup from ICAO code to station
  name, city, and country, kept as data rather than code.
- **Wind shear and runway state groups**: model the remaining standard
  groups so `unparsed` comes back empty for well-formed reports.
- **Batch and file input**: decode a file of reports, one per line, for
  log analysis and climatology studies.

If you build one of these, open an issue or a pull request. Include the
raw report string that motivated the change: with METAR, the string is
the test case.

## Project structure

```text
src/metar_decoder/   the package (parser, codes, report, cli)
tests/               pytest suite, field-level checks per report
examples/            runnable script decoding five sample reports
.github/workflows/   CI: install and run the test suite on every push
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: fork, branch,
test, pull request. Every change should keep `pytest -q` green and should
not change a decoded value without explaining why in the PR.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE).

## Author

Sajid Kabir Saji, aeronautical engineer. Research interests: onboard
autonomous decision-making for UAVs and solar-electric flight endurance.
More at [sajidkabir.com](https://sajidkabir.com).
