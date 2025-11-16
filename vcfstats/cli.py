"""Powerful VCF statistics"""
import logging
import sys
from itertools import chain
from os import path

from argx import ArgumentParser
from cyvcf2 import VCF
from rich.console import Console
from rich.table import Table
from simpleconf import Config

from .instance import Instance
from .utils import HERE, MACROS, DEVPARS_DEFAULTS, capture_c_msg, logger


def _check_len_callback(value, allvalues, name):
    expect_len = len(allvalues.formula)
    if value and len(value) != expect_len:  # pragma: no cover
        return ValueError(f"Wrong length of {name}, expect {expect_len}.")
    return value


def get_params():
    """Get the parameter definitions"""
    from . import __version__

    params = ArgumentParser.from_configs(
        HERE / "args.toml",
        version=__version__,
    )
    return params


def get_vcf_by_regions(vcffile, regions):
    """Compile all the regions provided by use together,
    and return a chained iterator."""
    logger.info("Getting vcf handler by given regions ...")
    with capture_c_msg("cyvcf2"):
        vcf = VCF(str(vcffile), gts012=True)
        samples = vcf.samples
        if regions:
            if len(regions) == 1:
                vcf = vcf(regions[0])
            else:
                vcf2 = chain(vcf(regions[0]), vcf(regions[1]))
                for region in regions[2:]:
                    vcf2 = chain(vcf2, vcf(region))
                vcf = vcf2

    return vcf, samples


def combine_regions(regions, regfile):
    """Combine all the regions.
    Users have to make sure there is no overlapping between regions"""
    logger.info(
        "Combining regions, be reminded that regions should "
        "NOT be overlapping ..."
    )
    # make sure regions have no overlaps
    ret = regions[:] if regions else []
    if regfile:
        with open(regfile, "r") as freg:
            for line in freg:
                if line.startswith("#"):
                    continue
                parts = line.strip().split("\t")[:3]
                ret.append("{}:{}-{}".format(*parts))
    return ret


def get_instances(opts, samples, default_devpars):
    """Get instances/formulas. This will determine h
    ow many figures we are plotting"""
    logger.info("Getting instances ...")
    ret = []

    # opts.devpars
    # {"width": [1000, 1000], "height": [1000, 1000], "res": [100, 100]]}
    # to
    # [
    #   {"width": 1000, "height": 1000, "res": 100},
    #   {"width": 1000, "height": 1000, "res": 100}
    # ]
    ddevpars = DEVPARS_DEFAULTS.copy()
    ddevpars.update(default_devpars)

    for i, formula in enumerate(opts.formula):
        ggs = opts.ggs[i] if i < len(opts.ggs) else None
        figtype = opts.figtype[i] if i < len(opts.figtype) else None
        figfmt = opts.figfmt[i] if i < len(opts.figfmt) else None
        devpars = {
            k: v[i] if i < len(v) else ddevpars[k]
            for k, v in vars(opts.devpars).items()
        }
        devpars.setdefault("width", ddevpars["width"])
        devpars.setdefault("height", ddevpars["height"])
        devpars.setdefault("res", ddevpars["res"])

        ret.append(
            Instance(
                formula,
                opts.title[i],
                ggs,
                devpars,
                opts.outdir,
                samples,
                figtype,
                opts.passed,
                opts.savedata,
                figfmt or "png",
            )
        )
    return ret


def list_macros():
    """List the available macros, including user-provided ones"""
    table = Table(title="Available Macros")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Description")
    for name, macro in MACROS.items():
        table.add_row(name, macro.get("type", "-"), macro["func"].__doc__)
    Console().print(table)
    sys.exit(0)


def load_macrofile(macrofile):
    """Load the macros from a python file"""
    macrofile = str(macrofile)
    if not macrofile.endswith(".py"):
        macrofile = macrofile + ".py"
    if not path.isfile(macrofile):
        raise OSError("Macro file does not exist: {}".format(macrofile))
    import importlib.util

    spec = importlib.util.spec_from_file_location("mymacros", macrofile)
    spec.loader.exec_module(importlib.util.module_from_spec(spec))


def main():
    """Main entrance of the program"""
    # modify sys.argv to see if we have --list or -l option
    # If so, we ignore those required arguments
    if "-l" in sys.argv or "--list" in sys.argv:
        if "--macro" in sys.argv:
            load_macrofile(sys.argv[sys.argv.index("--macro") + 1])
        list_macros()

    params = get_params()
    default_devpars = {}
    if "--config" in sys.argv:
        configfile = sys.argv[sys.argv.index("--config") + 1]
        config = Config.load_one(configfile, loader="toml")
        instances = config.pop("instance", [])
        default_devpars = config.pop("devpars", {})
        for instance in instances:
            for key, val in instance.items():
                if key == "devpars":
                    config.setdefault(key, {})
                    value = DEVPARS_DEFAULTS.copy()
                    value.update(default_devpars)
                    value.update(val)
                    for k, v in value.items():
                        config["devpars"].setdefault(k, []).append(v)
                else:
                    config.setdefault(key, []).append(val)

        params.set_defaults_from_configs(config)

    opts = params.parse_args()
    _check_len_callback(opts.title, opts, name="title")
    _check_len_callback(opts.ggs, opts, name="ggs")
    logger.setLevel(getattr(logging, opts.loglevel.upper()))

    if opts.macro:
        load_macrofile(opts.macro)

    vcf, samples = get_vcf_by_regions(
        # TODO: should write to a different file instead of appending to
        # opts.Region
        opts.vcf, combine_regions(opts.region, opts.Region)
    )
    ones = get_instances(opts, samples, default_devpars)
    logger.info("Start reading variants ...")
    xi = 0
    with capture_c_msg("cyvcf2"):
        for i, variant in enumerate(vcf):
            xi = i
            for instance in ones:
                # save entries, cache aggr
                instance.iterate(variant, vcf)
            if i % 10000 == 0:  # pragma: no cover
                logger.debug("- %s variants read.", i)
    logger.info(
        "%s variants read.", xi
    )
    for i, instance in enumerate(ones):
        # save aggr
        instance.summarize()
        instance.plot()
