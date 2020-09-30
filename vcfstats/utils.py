"""Utilities for vcfstats"""
import logging
from os.path import commonprefix
from pathlib import Path
from rich.logging import RichHandler
from pyparam import defaults

defaults.HELP_OPTION_WIDTH = 28

# macro database
MACROS = {}

VCFSTATS_LOGGER_NAME = "VCFSTATS"

# where this file is located
HERE = Path(__file__).parent.resolve()

def parse_subsets(subsets: list):
    """Parse subsets written in short format"""
    ret = []
    for subset in subsets:
        if subset.count('-') == 1:
            start, end = subset.split('-')
            compref = commonprefix([start, end])
            if compref and compref[-1].isdigit():
                compref = compref[:-1]
            start = start[len(compref):]
            end = end[len(compref):]
            if start.isdigit() and end.isdigit() and int(start) < int(end):
                ret.extend([compref + str(i)
                            for i in range(int(start), int(end) + 1)])
            else:
                ret.append(subset)
        else:
            ret.append(subset)
    return ret

# pylint: disable=invalid-name
logger = logging.getLogger(VCFSTATS_LOGGER_NAME)
logger.setLevel(logging.INFO)
logger.addHandler(RichHandler(show_time=True, show_path=False))
