from pathlib import Path

import cmdy
import pytest
from argparse import Namespace

from vcfstats.cli import (
    MACROS,
    Instance,
    combine_regions,
    get_instances,
    get_vcf_by_regions,
    list_macros,
    load_macrofile,
    main,
)

HERE = Path(__file__).parent.resolve()


@pytest.fixture
def vcffile(tmp_path):
    ovcf = HERE.parent.joinpath("examples", "sample.vcf")
    nvcf = tmp_path.with_suffix(".vcf.gz")
    c = cmdy.bgzip(ovcf, c=True).r > nvcf
    cmdy.tabix(p="vcf", _=nvcf).fg
    return nvcf


def test_get_vcf_by_regions(vcffile):
    vcf, samples = get_vcf_by_regions(
        vcffile, ["1:10176-10251", "2:14900-15000", "3:16000-17000"]
    )
    assert len(list(vcf)) == 5
    assert samples == ["A", "B", "C", "D"]

    vcf, samples = get_vcf_by_regions(vcffile, ["1:10176-10251"])
    assert len(list(vcf)) == 2
    assert samples == ["A", "B", "C", "D"]


def test_combine_regions(tmp_path):
    bedfile = tmp_path.with_suffix(".bed")
    bedfile.write_text("#header\n3\t1\t1000\n4\t2\t2000\n")
    regions = combine_regions(["1:10176-10251", "2:14900-15000"], bedfile)
    assert regions == [
        "1:10176-10251",
        "2:14900-15000",
        "3:1-1000",
        "4:2-2000",
    ]


def test_get_ones(tmp_path):
    ones = get_instances(
        Namespace(
            **{
                "devpars": Namespace(
                    **{"width": [1000], "height": [1000], "res": [100]}
                ),
                "formula": ["COUNT(1) ~ CHROM", "AAF ~ CHROM"],
                "title": ["title1", "title2"],
                "ggs": [],
                "figtype": [],
                "passed": False,
                "outdir": tmp_path,
                "savedata": False,
                "figfmt": [],
            }
        ),
        ["A", "B", "C", "D"],
        {},
    )
    assert len(ones) == 2
    assert isinstance(ones[0], Instance)
    assert isinstance(ones[1], Instance)


def test_list_macros(capsys):
    with pytest.raises(SystemExit):
        list_macros()
    out = capsys.readouterr().out
    assert "COUNT" in out


def test_load_macrofile(tmp_path):
    macrofile = tmp_path.with_suffix(".macro.py")
    with pytest.raises(OSError):
        load_macrofile(tmp_path.with_suffix(".macro"))
    macrofile.write_text(
        """
from vcfstats.macros import cat
@cat
def DEMO(variant):
    return variant.CHROM
"""
    )
    load_macrofile(macrofile)
    assert "DEMO" in MACROS


def test_main(vcffile, tmp_path):
    # help
    cmd = cmdy.vcfstats(_raise=False).stderr
    assert "the following arguments are required" in str(cmd)

    macrofile = tmp_path.with_suffix(".macromain.py")
    macrofile.write_text(
        """
from vcfstats.macros import cat
@cat
def DEMO(variant):
    '''Some demo macro'''
    return variant.CHROM
"""
    )
    cmd = cmdy.vcfstats(l=True, macro=macrofile, _raise=False)
    assert "Return 1 for a variant" in cmd.stdout
    assert "Some demo macro" in cmd.stdout

    cmd = cmdy.vcfstats(
        vcf=vcffile,
        outdir=tmp_path,
        formula="COUNT(1) ~ CONTIG",
        title="Variants on each chromosome",
        config=HERE.parent.joinpath("examples", "config.toml"),
        _raise=False,
    )
    print(cmd.stderr, cmd.strcmd)
    assert cmd.rc == 0
