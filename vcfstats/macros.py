"""Builtin marcros for vcfstats"""
import warnings
from functools import partial

from .utils import MACROS


def categorical(func=None, alias=None, _name=None):
    """Categorical decorator"""
    if alias:
        return partial(categorical, _name=alias)
    funcname = func.__name__
    if funcname not in MACROS:
        MACROS[funcname] = {}
        MACROS[funcname]["func"] = MACROS[funcname].get("func", func)
        MACROS[funcname]["type"] = "categorical"
    if _name:
        MACROS[_name] = MACROS[funcname]
    return MACROS[funcname]["func"]


def continuous(func=None, alias=None, _name=None):
    """Continuous decorator"""
    if alias:
        return partial(continuous, _name=alias)
    funcname = func.__name__
    if funcname not in MACROS:
        MACROS[funcname] = {}
        MACROS[funcname]["func"] = MACROS[funcname].get("func", func)
        MACROS[funcname]["type"] = "continuous"
    if _name:
        MACROS[_name] = MACROS[funcname]
    return MACROS[funcname]["func"]


def aggregation(func=None, alias=None, _name=None):
    """Aggregation decorator"""
    if alias:
        return partial(aggregation, _name=alias)
    funcname = func.__name__
    if funcname not in MACROS:
        MACROS[funcname] = {}
        MACROS[funcname]["func"] = MACROS[funcname].get("func", func)
        MACROS[funcname]["aggr"] = True
    if _name:
        MACROS[_name] = MACROS[funcname]
    return MACROS[funcname]["func"]


cat = categorical
cont = continuous
aggr = aggregation


@categorical
def VARTYPE(variant):
    """Variant type, one of deletion, indel, snp or sv"""
    return variant.var_type


@categorical
def TITV(variant):
    """Tell if a variant is a transition or transversion.
    The variant has to be an snp first."""
    if not variant.is_snp:
        return False
    return "transition" if variant.is_transition else "transversion"


@categorical(alias="CHROM")
def CONTIG(variant):
    """Get the config/chromosome of a variant. Alias: CHROM"""
    return variant.CHROM


@categorical(alias="GT_TYPEs")
def GTTYPEs(variant):
    """Get the genotypes(HOM_REF,HET,HOM_ALT,UNKNOWN)
    of a variant for each sample"""
    gttypes = variant.gt_types
    return [
        "HOM_REF"
        if gttype == 0
        else "HET"
        if gttype == 1
        else "HOM_ALT"
        if gttype == 2
        else "UNKNOWN"
        for gttype in gttypes
    ]


@categorical
def FILTER(variant):
    """Get the FILTER of a variant."""
    return variant.FILTER or "PASS"


@categorical
def SUBST(variant):
    """Substitution of the variant, including all types of varinat"""
    return "{}>{}".format(variant.REF, ",".join(variant.ALT))


@categorical
def SAMPLES(variant):
    """Get the sample indices"""
    return list(range(len(variant.genotypes)))


@continuous
def NALT(variant):
    """Number of alternative alleles"""
    return len(variant.ALT)


@continuous
def GQs(variant):
    """get the GQ for each sample as a numpy array."""
    return variant.gt_quals


@continuous
def QUAL(variant):
    """Variant quality from QUAL field."""
    return variant.QUAL


@continuous(alias="DPs")
def DEPTHs(variant):
    """Get the read-depth for each sample as a numpy array."""
    try:
        return [sum(dp) for dp in variant.format("DP")]
    except (TypeError, ValueError):
        warnings.warn(
            "Failed to fetch sample depth for variant: {}".format(
                variant
            ).rstrip("\n"),
            stacklevel=0,
        )
        return None


@continuous
def AAF(variant):
    """Alternate allele frequency across samples in this VCF."""
    return variant.aaf


@continuous
def AFs(variant):
    """get the freq of alternate reads as a numpy array."""
    return variant.gt_alt_freqs


@continuous
def _ONE(variant):
    """Return 1 for a variant, usually used in aggregation,
    or indication of a distribution plot"""
    return 1


@aggregation
def COUNT(entries):
    """Count the variants in groups"""
    return len(entries)


@aggregation
def SUM(entries):
    """Sum up the values in groups"""
    return sum(entries)


@aggregation(alias="AVG")
def MEAN(entries):
    """Get the mean of the values"""
    if not entries:
        return 0.0
    return sum(entries) / len(entries)
