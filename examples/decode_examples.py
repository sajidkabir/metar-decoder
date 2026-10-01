"""Decode a set of real-world style METAR reports and print the summaries.

Run from the repository root after ``pip install -e .``:

    python examples/decode_examples.py
"""

from metar_decoder import human_readable, parse_metar

SAMPLES = [
    # Dhaka, hazy afternoon.
    "VGHS 011200Z 18008KT 4000 HZ SCT018 BKN100 31/27 Q1006 NOSIG",
    # New York JFK, gusty with a remarks section.
    "KJFK 011751Z 31012G24KT 10SM FEW045 SCT250 24/13 A2992 RMK AO2",
    # Hong Kong, heavy thunderstorm with rain and cumulonimbus.
    "VHHH 011230Z 24015G30KT 2500 +TSRA SCT015CB BKN040 26/24 Q1002 TEMPO",
    # London Heathrow, fog, obscured sky, below freezing.
    "EGLL 010550Z 05003KT 0300 FG VV001 M01/M01 Q1030 NOSIG",
    # Dubai, CAVOK and hot.
    "OMDB 011200Z 32006KT CAVOK 38/24 Q1009 NOSIG",
]


def main():
    for raw in SAMPLES:
        print(raw)
        print(human_readable(parse_metar(raw)))
        print()


if __name__ == "__main__":
    main()
