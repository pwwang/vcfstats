"""Utilities for vcfstats"""
import logging
from rich.logging import RichHandler

# macro database
MACROS = {}

VCFSTATS_LOGGER_NAME = "VCFSTATS"

# pylint: disable=invalid-name
logger = logging.getLogger(VCFSTATS_LOGGER_NAME)
logger.setLevel(logging.INFO)
logger.addHandler(RichHandler(show_time=True, show_path=False))
