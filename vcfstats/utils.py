"""Utilities for vcfstats"""
import logging
from pathlib import Path
from rich.logging import RichHandler
from pyparam import defaults

defaults.HELP_OPTION_WIDTH = 28

# macro database
MACROS = {}

VCFSTATS_LOGGER_NAME = "VCFSTATS"

# where this file is located
HERE = Path(__file__).parent.resolve()



# pylint: disable=invalid-name
logger = logging.getLogger(VCFSTATS_LOGGER_NAME)
logger.setLevel(logging.INFO)
logger.addHandler(RichHandler(show_time=True, show_path=False))
