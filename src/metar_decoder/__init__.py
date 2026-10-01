"""metar-decoder: decode METAR aviation weather reports into plain English.

Pure standard library, no runtime dependencies.
"""

from .parser import MetarReport, parse_metar
from .report import human_readable

__version__ = "1.0.0"

__all__ = ["MetarReport", "parse_metar", "human_readable", "__version__"]
