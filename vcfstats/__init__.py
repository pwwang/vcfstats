"""Powerful VCF statistics"""
import sys
import logging
from os import path
from pathlib import Path
from functools import partial
from itertools import chain
from simpleconf import Config
from cyvcf2 import VCF
from pyparam import Params, defaults
MACROS = {}
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)-15s %(levelname)5s] %(message)s')
LOGGER = logging.getLogger(__name__)
from . import macros  # pylint:disable=wrong-import-position
from .one import One  # pylint:disable=wrong-import-position

__version__ = "0.0.6"

HERE = Path(__file__).parent.resolve()
defaults.HELP_OPTION_WIDTH = 28

def _list_callback(value, allvalues, params): # pylint:disable=unused-argument
    if not value:
        return False
    for param in ('vcf', 'outdir', 'formula', 'title'):
        params.get_param(param).required = False
    return True

def _check_len_callback(value, allvalues, name):
    expect_len = len(allvalues.formula)
    if value and len(value) != expect_len:
        return ValueError(f"Wrong length of {name}, expect {expect_len}.")
    return value

def get_params():
    """Get the parameter definitions"""
    params = Params(prog='vcfstats',
                    desc=f'vcfstats v{__version__}: Powerful VCF statistics.')
    params.from_file(HERE / 'args.toml')
    params.get_param('list').callback = partial(_list_callback, params=params)
    params.get_param('title').callback = partial(_check_len_callback,
                                                 name='title')
    params.get_param('ggs').callback = partial(_check_len_callback, name='ggs')
    return params

def get_vcf_by_regions(vcffile, regions):
    """Compile all the regions provided by use together,
    and return a chained iterator."""
    LOGGER.info("Getting vcf handler by given regions ...")
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
    LOGGER.info(
        "Combining regions, remind that regions should not be overlapping ...")
    # make sure regions have no overlaps
    ret = regions[:] if regions else []
    if regfile:
        with open(regfile, 'r') as freg:
            for line in freg:
                if line.startswith('#'):
                    continue
                parts = line.strip().split('\t')[:3]
                ret.append('{}:{}-{}'.format(*parts))
    return ret


def get_ones(opts, samples):
    """Get instances/formulas. This will determine h
    ow many figures we are plotting"""
    LOGGER.info("Getting instances ...")
    ret = []
    devpars = opts['devpars']
    if not isinstance(devpars, list):
        devpars = [devpars] * len(opts['formula'])
    for i, formula in enumerate(opts['formula']):
        ggs = opts['ggs'][i] if i < len(opts['ggs']) else None
        figtype = opts['figtype'][i] if i < len(opts['figtype']) else None
        ret.append(
            One(formula, opts['title'][i], ggs, devpars[i], opts['outdir'],
                samples, figtype, opts['passed']))
    return ret


def list_macros():
    """List the available macros, including user-provided ones"""
    for name, macro in MACROS.items():
        print(name.ljust(10), "|", macro.get('type', '').ljust(15), "|",
              macro['func'].__doc__)
    sys.exit(0)

def load_macrofile(macrofile):
    """Load the macros from a python file"""
    macrofile = str(macrofile)
    if not macrofile.endswith('.py'):
        macrofile = macrofile + '.py'
    if not path.isfile(macrofile):
        raise OSError("Macro file does not exist: {}".format(macrofile))
    import importlib.util
    spec = importlib.util.spec_from_file_location("mymacros", macrofile)
    spec.loader.exec_module(importlib.util.module_from_spec(spec))


def load_config(config, opts):
    """Load the configurations from file"""
    if not path.isfile(config):
        raise OSError("Config file does not exist: {}".format(config))
    configs = Config(with_profile=False)
    configs._load(config)
    configs = configs.as_dict()
    ones = []
    if 'one' in configs:
        ones = configs['one']
        del configs['one']
    opts |= configs
    # padding figtype and ggs, and devpars
    len_fml = len(opts['formula'])
    opts['figtype'].extend([None] * (len_fml - len(opts['figtype'])))
    opts['ggs'].extend([None] * (len_fml - len(opts['ggs'])))
    if isinstance(opts['devpars'], list):
        default_devpars = opts['devpars'][0]
        opts['devpars'].extend([default_devpars] *
                               (len_fml - len(opts['devpars'])))
    else:
        default_devpars = opts['devpars']
        opts['devpars'] = [opts['devpars']] * len_fml
    for one in ones:
        if 'formula' not in one:
            raise ValueError("Formula not found in instance: {}".format(one))
        if 'title' not in one:
            raise ValueError("Title not found in instance: {}".format(one))
        opts['formula'].append(one['formula'])
        opts['title'].append(one['title'])
        opts['figtype'].append(one.get('figtype'))
        opts['ggs'].append(one.get('ggs'))
        def_devpars = default_devpars.copy()
        def_devpars.update(one.get('devpars', {}))
        opts['devpars'].append(def_devpars)


def main():
    """Main entrance of the program"""
    params = get_params()
    # modify sys.argv to see if we have --list or -l option
    # If so, we ignore those required arguments
    if '-l' in sys.argv or '--list' in sys.argv:
        if '--macro' in sys.argv:
            load_macrofile(sys.argv[sys.argv.index('--macro') + 1])
        list_macros()

    opts = params.parse()
    LOGGER.setLevel(getattr(logging, opts['loglevel'].upper()))
    if opts['config']:
        load_config(opts['config'], opts)
    if opts['macro']:
        load_macrofile(opts['macro'])
    vcf, samples = get_vcf_by_regions(
        opts['vcf'], combine_regions(opts['region'], opts['Region']))
    ones = get_ones(opts, samples)
    LOGGER.info('Start reading variants ...')
    for i, variant in enumerate(vcf):
        for one in ones:
            # save entries, cache aggr
            one.iterate(variant)
        if i % 10000 == 0:  # pragma: no cover
            LOGGER.debug("- %s variants read.", i)
    LOGGER.info('%s variants read.', i)  # pylint: disable=undefined-loop-variable
    for i, one in enumerate(ones):
        # save aggr
        one.summarize()
        one.plot(opts['Rscript'])
