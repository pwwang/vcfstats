from vcfstats.macros import continuous


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
