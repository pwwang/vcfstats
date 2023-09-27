from pathlib import Path

import pytest
from cyvcf2 import VCF

from vcfstats.macros import (
    cat,
    _ONE,
    TITV,
    VARTYPE,
    CONTIG,
    AAF,
    AFs,
    COUNT,
    DEPTHs,
    FILTER,
    GTTYPEs,
    GQs,
    NALT,
    QUAL,
    SUBST,
    SAMPLES,
    MEAN,
    SUM,
)

HERE = Path(__file__).parent.resolve()


@cat
def mixedinfo(variant, vcf):
    """Global position of the variant"""
    return vcf.raw_header[:6] + variant.CHROM


@pytest.fixture(scope="module")
def variants():
    vcf = VCF(
        str(HERE.parent.joinpath("examples", "sample.vcf")),
        gts012=True,
    )
    return list(vcf)


@pytest.fixture(scope="module")
def variants_vcf():
    vcf = VCF(
        str(HERE.parent.joinpath("examples", "sample.vcf")),
        gts012=True,
    )
    return list(vcf), vcf


def test_variant_vcf(variants_vcf):
    assert mixedinfo(variants_vcf[0][0], variants_vcf[1]) == "##file1"


def test_vartype(variants):
    assert VARTYPE(variants[0]) == "snp"
    assert VARTYPE(variants[1]) == "snp"
    assert VARTYPE(variants[3]) == "indel"


def test_titv(variants):
    assert TITV(variants[0]) == "transversion"
    assert TITV(variants[1]) == "transversion"
    assert TITV(variants[5]) == "transition"
    assert TITV(variants[3]) is False


def test_contig(variants):
    assert CONTIG(variants[0]) == "1"
    assert CONTIG(variants[13]) == "2"


def test_gttypes(variants):
    assert GTTYPEs(variants[6]) == ["HET", "HOM_ALT", "HOM_REF", "HOM_REF"]


def test_filter(variants):
    assert FILTER(variants[0]) == "MinMQ"
    assert FILTER(variants[5]) == "PASS"


def test_subst(variants):
    assert SUBST(variants[0]) == "A>C"
    assert SUBST(variants[3]) == "ACCCC>ACCC"


def test_nalt(variants):
    assert NALT(variants[0]) == 1
    assert NALT(variants[1]) == 1
    assert NALT(variants[6]) == 2


def test_gqs(variants):
    assert list(GQs(variants[0])) == [5, 40, 83, 36]


def test_qual(variants):
    assert QUAL(variants[0]) == 37


def test_dps(variants):
    assert list(DEPTHs(variants[0])) == [101, 51, 85, 85]


def test_aaf(variants):
    assert AAF(variants[0]) == 0.125
    assert AAF(variants[2]) == 0.25


def test_afs(variants):
    # no AF in format in sample.vcf
    assert list(AFs(variants[0])) == [-1, -1, -1, -1]


def test_one(variants):
    assert _ONE(None) == 1


def test_samples(variants):
    assert list(SAMPLES(variants[0])) == [0, 1, 2, 3]


@pytest.mark.parametrize("entries", ([], [1, 2], [1, 2, 3]))
def test_count(entries):
    assert COUNT(entries) == len(entries)


@pytest.mark.parametrize("entries", ([], [1, 2], [1, 2, 3]))
def test_sum(entries):
    assert SUM(entries) == sum(entries)


@pytest.mark.parametrize(
    "entries, expected", [([], 0), ([1, 2], 1.5), ([1, 2, 3], 2)]
)
def test_mean(entries, expected):
    assert MEAN(entries) == expected
