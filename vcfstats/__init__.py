"""Powerful VCF statistics"""
import logging
from os import path
from itertools import chain
from cyvcf2 import VCF
from pyparam import params, Params
MACROS = {}
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)-15s %(levelname)5s] %(message)s')
LOGGER = logging.getLogger(__name__)
from . import macros  # pylint:disable=wrong-import-position
from .one import One  # pylint:disable=wrong-import-position

__version__ = "0.0.5"

params._desc = 'vcfstats v{}: Powerful VCF statistics.'.format(__version__)

params.vcf.required = True
params.vcf.desc = 'The VCF file'
params.v = params.vcf
params.loglevel = 'INFO'
params.loglevel.desc = 'The logging level.'
params.outdir.required = True
params.outdir.desc = 'The output directory.'
params.o = params.outdir
params.Rscript = 'Rscript'
params.Rscript.desc = 'Path to Rscript to run R code for plotting.'
params.figtype = []
params.figtype.desc = 'Your preferences for types of plots for each formula.'
params.r = []
params.r.desc = 'Regions in format of [CHR] or [CHR]:[START]-[END]'
params.region = params.r
params.R.desc = ['Regions in a BED file',
                 'If both -r/R are provided, regions will be merged.']
params.Region = params.R
params.p = False
params.p.desc = [
    'Only analyze variants that pass all filters.',
    'This does not work if FILTER entry is in the analysis.'
]
params.passed = params.p
params.l = False
params.l.desc = 'List all available macros.'
params.macro.desc = 'User-defined macro file.'
params.list = params.l
params.f.type = list
params.f.required = True
params.f.desc = [
    'The formulas for plotting in format of [Y] ~ [X],',
    'where [Y] or [X] should be an entry or an aggregation'
]
params.formula = params.f
params.t.type = list
params.t.required = True
params.t.desc = ('The title of each figure, '
                 'will be used to name the output files.')
params.title = params.t
params.ggs = []
params.ggs.desc = 'Extra ggplot2 expression for each plot'
params.devpars = dict(width=2000, height=2000, res=300)
params.devpars.desc = [
    'The device parameters for plots.',
    'To specify devpars for each plot, use a configuration file.'
]
params.c.desc = [
    'A configuration file defining how to plot in TOML format.',
    'If this is provided, CLI arguments will be overwritten '
    'if defined in this file.'
]
params.config = params.c

params.l.callback = lambda opt, pms: (pms.vcf.set_value('vcf')
                                      and pms.outdir.set_value('outdir')
                                      and pms.f.set_value(['f'])
                                      and pms.t.set_value(['t'])
                                      if opt.value
                                      else None)

params.t.callback = lambda opt, pms: (
    'Wrong length of title (expect {}, got {})'.format(len(pms.f.value or []),
                                                       len(opt.value or []))
    if len(opt.value or []) != len(pms.f.value or [])
    else None
)

params.ggs.callback = lambda opt, pms: (
    'Wrong length of ggs'
    if (len(opt.value or []) > 1
        and len(opt.value or []) != len(pms.f.value or []))
    else None
)


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
    macropage = Params()

    def helpx(helps):
        helps.remove('Usage')
        helps.remove('Optional options')
        helps.add('Continuous terms', sectype='option')
        helps.add('Categorical terms', sectype='option')
        helps.add('Aggregations', sectype='option')
        for name, macro in MACROS.items():
            if name == '_ONE':
                name = '1'
            if macro.get('aggr'):
                helps.select('Aggregations').add(
                    (name, '', macro['func'].__doc__ or ''))
            elif macro['type'] == 'continuous':
                helps.select('Continuous').add((name, '', macro['func'].__doc__
                                                or ''))
            else:
                helps.select('Categorical').add(
                    (name, '', macro['func'].__doc__ or ''))

    macropage._helpx = helpx
    macropage._help(print_and_exit=True)


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
    configs = Params()
    configs._load_file(config)
    configs = configs._as_dict()
    ones = []
    if 'one' in configs:
        ones = configs['one']
        del configs['one']
    opts.update(configs)
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
    opts = params._parse()
    LOGGER.setLevel(getattr(logging, opts['loglevel'].upper()))
    if opts['config']:
        load_config(opts['config'], opts)
    if opts['macro']:
        load_macrofile(opts['macro'])
    if opts['l']:
        list_macros()
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
