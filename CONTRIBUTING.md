# Contributing

Contributions are welcome: bug reports, decoding corrections, new group
types, documentation, and examples. This project aims to stay small,
readable, dependency free, and honest about what it does not yet decode.

## Getting set up

```bash
git clone https://github.com/sajidkabir/metar-decoder.git
cd metar-decoder
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest
pytest -q
```

All tests should pass before you change anything. The package is pure
standard library, so there is nothing else to install.

## Making a change

1. Fork the repository and create a branch from `main`
   (`git checkout -b feature/short-name`).
2. Keep the change focused. One group type, one fix, or one feature per
   pull request.
3. Add or update tests. Decoding changes need a check against a real or
   realistic report, and the test should say which field of which report
   pins the behavior down.
4. Run `pytest -q` and make sure it is green.
5. Update the README, the docstrings, and `CHANGELOG.md` (Unreleased
   section) if behavior or output changes.
6. Open a pull request against `main` describing what changed, why, and
   what it does to the decoded output for the example reports.

## Ground rules

- No silent changes to decoded values. If a fix changes a number or a
  phrase, say so in the pull request and in the changelog.
- No new runtime dependencies. The standard library is enough for this
  problem, and staying dependency free is a feature.
- Unrecognized groups are preserved in the report's `unparsed` list, never
  silently dropped. If you teach the parser a new group, move it out of
  `unparsed` and into a typed field.
- Groups the parser does not model yet belong in the README limitations
  list until they are decoded.

## Reporting issues

Open an issue with the raw METAR string, the output you got, and the output
you expected. The raw string alone is usually enough to reproduce the
problem, which makes METAR bugs unusually pleasant to report.
