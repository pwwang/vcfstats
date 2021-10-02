"""Utilities for vcfstats"""
import logging
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO
from os.path import commonprefix
from pathlib import Path

import py
from pyparam import defaults
from rich.logging import RichHandler

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
        subset = str(subset)
        if subset.count("-") == 1:
            start, end = subset.split("-")
            compref = commonprefix([start, end])
            if compref and compref[-1].isdigit():
                compref = compref[:-1]
            start = start[len(compref) :]
            end = end[len(compref) :]
            if start.isdigit() and end.isdigit() and int(start) < int(end):
                ret.extend(
                    [compref + str(i) for i in range(int(start), int(end) + 1)]
                )
            else:
                ret.append(subset)
        else:
            ret.append(subset)
    return ret


logger = logging.getLogger(VCFSTATS_LOGGER_NAME)
logger.setLevel(logging.INFO)
logger.addHandler(
    RichHandler(show_time=True, show_path=False, omit_repeated_times=False)
)


@contextmanager
def capture_c_msg(
    name, stdout_level="info", stderr_level="warning", prefix=""
):
    """Capture stdout/err from cyvcf2, which is c-level outputs that
    cannot be captured by redirect_stdout/err"""
    stdout_log = getattr(logger, stdout_level)
    stderr_log = getattr(logger, stderr_level)
    g_exc = None
    capture = py.io.StdCaptureFD(out=False, in_=False)
    try:
        yield
    except Exception as exc:
        g_exc = exc
    out, err = capture.reset()
    outs = out.rstrip().splitlines()
    errs = err.rstrip().splitlines()
    for out in outs:
        stdout_log(
            "%s(%s) [dim]%s[/dim]",
            prefix,
            name,
            out,
            extra={"markup": True},
        )
    for err in errs:
        stderr_log(
            "%s(%s) [dim]%s[/dim]",
            prefix,
            name,
            err,
            extra={"markup": True},
        )
    if g_exc:
        raise g_exc


@contextmanager
def capture_python_msg(
    name,
    stdout_level="info",
    stderr_level="warning",
    prefix="",
):
    outio = StringIO()
    errio = StringIO()
    stdout_log = getattr(logger, stdout_level)
    stderr_log = getattr(logger, stderr_level)
    with redirect_stdout(outio), redirect_stderr(errio):
        yield

    outs = outio.getvalue().rstrip().splitlines()
    errs = errio.getvalue().rstrip().splitlines()
    for out in outs:
        stdout_log(
            "%s(%s) [dim]%s[/dim]",
            prefix,
            name,
            out,
            extra={"markup": True},
        )
    for err in errs:
        stderr_log(
            "%s(%s) [dim]%s[/dim]",
            prefix,
            name,
            err,
            extra={"markup": True},
        )
