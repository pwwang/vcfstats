from io import StringIO
from pathlib import Path

import pytest
from cyvcf2 import VCF

from vcfstats.formula import Aggr, Formula, One, Term, parse_subsets
from vcfstats.macros import cat
from vcfstats.utils import MACROS

HERE = Path(__file__).parent.resolve()


@pytest.fixture(scope="module")
def variants():
    vcf = VCF(
        str(HERE.parent.joinpath("examples", "sample.vcf")),
        gts012=True,
    )
    return list(vcf) + [vcf.samples]


@cat
def FILTER2(variant):
    return variant.FILTER


@pytest.mark.parametrize(
    "subsets,expected",
    [
        (["a", "b", "c"], ["a", "b", "c"]),
        (["1-8", "12"], ["1", "2", "3", "4", "5", "6", "7", "8", "12"]),
        (
            ["chr1-chr10", "a-b"],
            [
                "chr1",
                "chr2",
                "chr3",
                "chr4",
                "chr5",
                "chr6",
                "chr7",
                "chr8",
                "chr9",
                "chr10",
                "a-b",
            ],
        ),
    ],
)
def test_parse_subsets(subsets, expected):
    assert parse_subsets(subsets) == expected


# @pytest.mark.parametrize('string, delimit, trim, expect', [
# 	("a\"|\"b", "|", True, ["a\"|\"b"]),
# 	("a|b|c", "|", True, ["a", "b", "c"]),
# 	('a|b\\|c', "|", True, ["a", "b\\|c"]),
# 	('a|b\\|c|(|)', "|", True, ["a", "b\\|c", "(|)"]),
# 	('a|b\\|c|(\\)|)', "|", True, ["a", "b\\|c", "(\\)|)"]),
# 	('a|b\\|c|(\\)\\\'|)', "|", True, ["a", "b\\|c", "(\\)\\'|)"]),
# 	('a|b\\|c |(\\)\\\'|)', "|", False, ["a", "b\\|c ", "(\\)\\'|)"]),
# 	('outdir:dir:{{i.pattern | lambda x: __import__("glob").glob(x)[0] | fn }}_etc', ':', True, ["outdir", "dir", "{{i.pattern | lambda x: __import__(\"glob\").glob(x)[0] | fn }}_etc"]),
# ])
# def test_safe_split(string, delimit, trim, expect):
# 	assert safe_split(string, delimit, trim) == expect


def test_term_init():
    term = Term("AAF", None)
    assert term.name == "AAF"
    assert term.term == MACROS["AAF"]
    assert term.samples == None
    assert term.subsets == None

    term = Term("AAF", items=[".05", ".95"])
    assert term.subsets == [0.05, 0.95]

    term = One()
    assert term.name == "_ONE"

    with pytest.raises(ValueError):
        Term("NoSuchTerm", None)

    MACROS["NOTYPE"] = {}
    with pytest.raises(TypeError):
        Term("NOTYPE", None)
    del MACROS["NOTYPE"]

    term = Term("AFs", samples=["1"])
    assert term.samples == ["1"]

    term = Term("AFs", [None, 0.5], ["sample2"])
    term.set_samples(["sample1", "sample2"])
    assert term.samples == [1]
    assert term.subsets == [None, 0.5]

    term2 = Term("AFs", [None, 0.5], ["sample2"])
    term2.set_samples(["sample1", "sample2"])
    assert term2.samples == [1]
    assert term2.subsets == [None, 0.5]
    assert repr(term2) == "<Term AFs(subsets=[None, 0.5], samples=[1])>"
    assert term2 == term
    assert term2 != 1

    with pytest.raises(KeyError):
        Term("AFs", [1, 2, 3], None)


def test_term_run(variants):
    term = Term("FILTER", "PASS")
    assert term.run(variants[0], passed=True) == False
    assert term.run(variants[5], passed=True) == ["PASS"]

    term = Term("FILTER2")
    assert term.run(variants[5], passed=True) == False

    term = Term("GTTYPEs", None, ["0"])
    term.set_samples(variants[-1])
    assert term.run(variants[0], passed=False) == ["HOM_REF"]

    term = Term("AAF", [0.126, None])
    # .125
    assert term.run(variants[0], passed=False) == False
    assert term.run(variants[2], passed=False) == [0.25]
    term = Term("AAF", [None, 0.24])
    # .25
    assert term.run(variants[0], passed=False) == [0.125]
    assert term.run(variants[2], passed=False) == False

    term = Term("FILTER", "PASS")
    assert term.run(variants[0], passed=False) == False
    assert term.run(variants[5], passed=False) == ["PASS"]


def test_aggr_init():
    with pytest.raises(ValueError):
        Aggr("COUNT", None)
    with pytest.raises(ValueError):
        Aggr("NoSuchAggr", "")
    aggr = Aggr("COUNT", One())
    assert aggr.term == One()
    assert aggr.filter is None
    assert aggr.group is None
    assert not aggr.has_filter()

    aggr = Aggr("COUNT", One(), Term("FILTER", ["PASS"]))
    assert aggr.term == One()
    assert aggr.group == Term("FILTER", ["PASS"])
    assert aggr.filter is None

    aggr = Aggr("COUNT", One(), filter=Term("FILTER", ["PASS"]))
    assert aggr.term == One()
    assert aggr.filter == Term("FILTER", ["PASS"])
    assert aggr.group is None
    assert aggr.has_filter()
    aggr.setxgroup(Term("VARTYPE", None))
    assert aggr.group == Term("VARTYPE", None)
    assert aggr.xgroup is None

    aggr = Aggr(
        "COUNT", One(), filter=Term("FILTER", ["PASS"]), group=Term("VARTYPE")
    )
    assert aggr.term == One()
    assert aggr.filter == Term("FILTER", ["PASS"])
    assert aggr.group == Term("VARTYPE", None)
    assert aggr.xgroup is None
    aggr.setxgroup(Term("GTTYPEs", ["A"]))
    assert aggr.xgroup == Term("GTTYPEs", ["A"])
    assert (
        repr(aggr)
        == "<Aggr COUNT(<Term _ONE()>, filter=<Term FILTER(subsets=['PASS'])>, group=<Term VARTYPE()>)>"
    )
    assert aggr.has_filter()

    aggr = Aggr("COUNT", One(), filter=Term("FILTER"), group=Term("VARTYPE"))
    assert aggr.term == One()
    assert aggr.filter == Term("FILTER", None)
    assert aggr.group == Term("VARTYPE", None)

    aggr = Aggr("COUNT", One(), filter=Term("GTTYPEs"))
    assert aggr.term == One()
    assert aggr.filter == Term("GTTYPEs", None)
    assert aggr.group == None

    with pytest.raises(ValueError):
        Aggr("Nosuchaggr", 1)

    with pytest.raises(ValueError):
        Aggr("COUNT", None)


def test_aggr_run(variants):
    aggr = Aggr(
        "COUNT", One(), filter=Term("FILTER", ["PASS"]), group=Term("VARTYPE")
    )
    aggr.run(variants[0], passed=True)
    assert len(aggr.cache) == 0

    aggr2 = Aggr("COUNT", One(), filter=Term("FILTER", ["PASS"]))
    with pytest.raises(RuntimeError):
        aggr2.run(variants[5], passed=True)

    aggr3 = Aggr(
        "COUNT", One(), filter=Term("FILTER", ["PASS"]), group=Term("FILTER2")
    )
    aggr3.run(variants[5], passed=False)
    assert len(aggr3.cache) == 0

    aggr4 = Aggr("COUNT", One(), Term("GTTYPEs"))
    with pytest.raises(ValueError):
        aggr4.run(variants[0], passed=False)

    aggr5 = Aggr("COUNT", One(), Term("VARTYPE"))
    aggr5.run(variants[0], passed=False)
    assert aggr5.cache == {"snp": [1]}
    aggr5.run(variants[1], passed=False)
    assert aggr5.cache == {"snp": [1, 1]}
    aggr5.run(variants[3], passed=False)
    assert aggr5.cache == {"snp": [1, 1], "indel": [1]}

    assert aggr5.dump() == {"snp": 2, "indel": 1}

    aggr5.cache.clear()
    aggr5.setxgroup(Term("FILTER", None))
    aggr5.run(variants[0], passed=False)
    assert aggr5.cache == {"MinMQ": {"snp": [1]}}

    aggr5.cache.clear()
    aggr5.setxgroup(Term("FILTER2", None))
    aggr5.run(variants[0], passed=False)
    assert aggr5.cache == {"MinMQ": {"snp": [1]}}
    aggr5.run(variants[5], passed=False)
    assert aggr5.cache == {"MinMQ": {"snp": [1]}}
    aggr5.run(variants[1], passed=False)
    assert aggr5.cache == {"MinMQ": {"snp": [1, 1]}}
    assert aggr5.dump() == {"MinMQ": [(2, "snp")]}

    aggr5.setxgroup(Term("GTTYPEs", ["HOM_REF", "HET"]))
    with pytest.raises(ValueError):
        aggr5.run(variants[0], passed=False)

    aggr6 = Aggr("MEAN", Term("AAF", [".2", None]), Term("CHROM"))
    aggr6.run(variants[0], passed=False)  # .125
    assert len(aggr6.cache) == 0


def test_formula_init():
    fmula = Formula("AAF", None, False, "title")
    assert fmula.Y == Term("AAF", None)
    assert fmula.X == One()

    fmula = Formula("AAF~", None, False, "title")
    assert fmula.Y == Term("AAF", None)
    assert fmula.X == One()

    fmula = Formula("MEAN(AAF) ~ CHROM", None, True, "title")
    assert fmula.Y.group == Term("CHROM", None)
    assert fmula.passed

    fmula = Formula("MEAN(AAF) ~ FILTER", None, True, "title")
    assert not fmula.passed

    fmula = Formula(
        "MEAN(AAF, FILTER[PASS], group=VARTYPE) ~ CHROM", None, True, "title"
    )
    assert isinstance(fmula.Y, Aggr)
    assert isinstance(fmula.X, Term)


def test_formula_run(variants):
    data = []
    fmula = Formula("AFs{0,1} ~ GTTYPEs{0-2}", variants[-1], False, "title")
    with pytest.raises(RuntimeError):
        fmula.run(variants[0], data.append, data.extend)

    fmula = Formula("FILTER2 ~ CHROM", variants[-1], False, "title")
    fmula.run(variants[5], data.append, data.extend)
    assert data == []

    fmula = Formula("GTTYPEs ~ CHROM", variants[-1], False, "title")
    fmula.run(variants[0], data.append, data.extend)
    assert data == [
        ("HOM_REF", "1"),
        ("HOM_REF", "1"),
        ("HOM_REF", "1"),
        ("HET", "1"),
    ]

    data = []
    fmula = Formula("CHROM ~ GTTYPEs", variants[-1], False, "title")
    fmula.run(variants[0], data.append, data.extend)
    assert data == [
        ("1", "HOM_REF"),
        ("1", "HOM_REF"),
        ("1", "HOM_REF"),
        ("1", "HET"),
    ]

    data = []
    fmula = Formula(
        "COUNT(1, filter=VARTYPE) ~ COUNT(1, filter=GTTYPEs, group=CHROM)",
        variants[-1],
        False,
        "title",
    )
    fmula.run(variants[0], data.append, data.extend)
    fmula.run(variants[1], data.append, data.extend)
    assert data == []
    fmula.done(data.append, data.extend)
    assert data == [(2, 2, "1")]

    data = []
    fmula = Formula(
        "COUNT(1, filter=VARTYPE) ~ COUNT(1, filter=GTTYPEs, group=CHROM)",
        variants[-1],
        False,
        "title",
    )
    fmula.run(variants[0], data.append, data.extend)
    assert data == []

    with pytest.raises(ValueError):
        Formula(
            "COUNT(1, filter=VARTYPE, group=GTTYPEs{0}) ~ COUNT(1, filter=GTTYPEs, group=CHROM)",
            ["A", "B", "C", "D"],
            False,
            "title",
        )

    fmula = Formula("COUNT(1) ~ CHROM", variants[-1], False, "title")
    fmula.run(variants[0], data.append, data.extend)
    fmula.run(variants[1], data.append, data.extend)
    assert data == []
    assert fmula.Y.cache == {"1": [1, 1]}
    fmula.done(data.append, data.extend)
    assert data == [(2, "1")]

    fmula = Formula("CHROM ~ COUNT(1)", variants[-1], False, "title")
    with pytest.raises(TypeError):
        fmula.run(variants[0], data.append, data.extend)

    data = []
    fmula = Formula(
        "COUNT(1, group = VARTYPE) ~ CHROM", variants[-1], False, "title"
    )
    fmula.run(variants[0], data.append, data.extend)
    fmula.run(variants[1], data.append, data.extend)
    fmula.run(variants[2], data.append, data.extend)
    fmula.run(variants[3], data.append, data.extend)
    fmula.done(data.append, data.extend)
    assert data == [(3, "1", "snp"), (1, "1", "indel")]
