from vcfstats.macros import continuous, categorical


@continuous
def INFO_DP(variant):
    """DP from INFO"""
    return variant.INFO["DP"]


@continuous
def MISSINGs(variant):
    """DP from INFO"""
    # convert boolean array to int
    # gts012 = True
    return (variant.gt_types == 3) + 0


@continuous
def N_MISSING(variant):
    """DP from INFO"""
    # convert boolean array to int
    # gts012 = True
    return variant.num_unknown


@continuous
def Percent_HETs(variant):
    """Get % of HETs per locus"""
    return variant.num_het / float(len(variant.gt_types))


@categorical
def Allelic_Type(variant):
    """Get allelic type, either biallelic or multiallelic"""
    return "biallelic" if len(variant.ALT) == 1 else "multi-allelic"


@categorical
def N_Allelic(variant):
    """Get number of alleles"""
    return len(variant.ALT) + 1
