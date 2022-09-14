"""Powerful VCF statistics"""
import logging
import sys
from functools import partial
from itertools import chain
from os import path

from cyvcf2 import VCF
from pyparam import Params, Namespace
from rich.console import Console
from rich.table import Table
from simpleconf import Config

from .instance import Instance
from .utils import HERE, MACROS, capture_c_msg, logger


def _check_len_callback(value, allvalues, name):
    expect_len = len(allvalues.formula)
    if value and len(value) != expect_len:
        return ValueError(f"Wrong length of {name}, expect {expect_len}.")
    return value


def get_params():
    """Get the parameter definitions"""
    from . import __version__

    params = Params(
        prog="vcfstats",
        desc=f"vcfstats v{__version__}: Powerful VCF statistics.",
    )
    params.from_file(HERE / "args.toml")
    params.get_param("title").callback = partial(
        _check_len_callback, name="title"
    )
    params.get_param("ggs").callback = partial(_check_len_callback, name="ggs")
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


def get_instances(opts, samples):
    """Get instances/formulas. This will determine h
    ow many figures we are plotting"""
    logger.info("Getting instances ...")
    ret = []
    devpars = opts["devpars"]
    if not isinstance(devpars, list):
        devpars = [devpars] * len(opts["formula"])
    for i, formula in enumerate(opts["formula"]):
        ggs = opts["ggs"][i] if i < len(opts["ggs"]) else None
        figtype = opts["figtype"][i] if i < len(opts["figtype"]) else None
        figfmt = opts["figfmt"][i] if i < len(opts["figfmt"]) else None

        if isinstance(devpars[i], Namespace):
            devpars[i] = vars(devpars[i])

        ret.append(
            Instance(
                formula,
                opts["title"][i],
                ggs,
                devpars[i],
                opts["outdir"],
                samples,
                figtype,
                opts["passed"],
                opts["savedata"],
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


def load_config(config, opts):
    """Load the configurations from file"""
    if not path.isfile(config):
        raise OSError("Config file does not exist: {}".format(config))
    configs = Config.load(config)
    configs = configs.as_dict()
    ones = []
    if "instance" in configs:
        ones = configs["instance"]
        del configs["instance"]
    opts |= configs
    # padding figtype and ggs, and devpars
    len_fml = len(opts["formula"])
    opts["figtype"].extend([None] * (len_fml - len(opts["figtype"])))
    opts["figfmt"].extend([None] * (len_fml - len(opts["figfmt"])))
    opts["ggs"].extend([None] * (len_fml - len(opts["ggs"])))
    if isinstance(opts["devpars"], list):
        default_devpars = opts["devpars"][0]
        opts["devpars"].extend(
            [default_devpars] * (len_fml - len(opts["devpars"]))
        )
    else:
        default_devpars = opts["devpars"]
        opts["devpars"] = [opts["devpars"]] * len_fml

    if isinstance(default_devpars, Namespace):
        default_devpars = default_devpars._to_dict()

    for instance in ones:
        if "formula" not in instance:
            raise ValueError(
                "Formula not found in instance: {}".format(instance)
            )
        if "title" not in instance:
            raise ValueError(
                "Title not found in instance: {}".format(instance)
            )
        opts["formula"].append(instance["formula"])
        opts["title"].append(instance["title"])
        opts["figtype"].append(instance.get("figtype"))
        opts["figfmt"].append(instance.get("figfmt"))
        opts["ggs"].append(instance.get("ggs"))
        def_devpars = default_devpars.copy()
        def_devpars.update(instance.get("devpars", {}))
        opts["devpars"].append(def_devpars)


def main():
    """Main entrance of the program"""
    params = get_params()
    # modify sys.argv to see if we have --list or -l option
    # If so, we ignore those required arguments
    if "-l" in sys.argv or "--list" in sys.argv:
        if "--macro" in sys.argv:
            load_macrofile(sys.argv[sys.argv.index("--macro") + 1])
        list_macros()

    opts = params.parse(ignore_errors=True)
    # title and formula can be optional if config file specified
    if "formula" in opts or "title" in opts:
        # raise other errors
        opts = params.parse()
    else:
        opts["formula"] = []
        opts["title"] = []

    if "ggs" not in opts:
        opts["ggs"] = []

    logger.setLevel(getattr(logging, opts["loglevel"].upper()))

    if opts["config"]:
        load_config(opts["config"], opts)

    if opts["macro"]:
        load_macrofile(opts["macro"])

    vcf, samples = get_vcf_by_regions(
        # TODO: should write to a different file instead of appending to
        # opts["Region"]
        opts["vcf"], combine_regions(opts["region"], opts["Region"])
    )

    ones = get_instances(opts, samples)
    logger.info("Start reading variants ...")
    with capture_c_msg("cyvcf2"):
        for i, variant in enumerate(vcf):
            for instance in ones:
                # save entries, cache aggr
                instance.iterate(variant)
            if i % 10000 == 0:  # pragma: no cover
                logger.debug("- %s variants read.", i)
    logger.info(
        "%s variants read.", i
    )
    for i, instance in enumerate(ones):
        # save aggr
        instance.summarize()
        instance.plot()
