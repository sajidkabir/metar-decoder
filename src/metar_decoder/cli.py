"""Command-line interface for metar-decoder.

Usage:
    metar decode "VGHS 011200Z 18008KT 4000 HZ SCT018 BKN100 31/27 Q1006 NOSIG"
    metar parse "VGHS 011200Z 18008KT 4000 HZ SCT018 BKN100 31/27 Q1006 NOSIG"
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from .parser import parse_metar
from .report import human_readable


def build_parser():
    parser = argparse.ArgumentParser(
        prog="metar",
        description="Decode METAR aviation weather reports.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    decode_parser = subparsers.add_parser(
        "decode", help="Print a plain-English summary of a METAR."
    )
    decode_parser.add_argument(
        "metar",
        nargs="+",
        help="The raw METAR string, quoted as one argument.",
    )

    parse_parser = subparsers.add_parser(
        "parse", help="Print the decoded METAR as JSON."
    )
    parse_parser.add_argument(
        "metar",
        nargs="+",
        help="The raw METAR string, quoted as one argument.",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    raw = " ".join(args.metar)
    try:
        report = parse_metar(raw)
    except ValueError as error:
        print("error: {}".format(error), file=sys.stderr)
        return 2

    if args.command == "decode":
        print(human_readable(report))
    elif args.command == "parse":
        print(json.dumps(dataclasses.asdict(report), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
