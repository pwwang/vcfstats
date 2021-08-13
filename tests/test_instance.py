import pytest
from pathlib import Path
from vcfstats.formula import Formula
from vcfstats.instance import title_to_valid_path, get_plot_type, Instance


@pytest.fixture
def instance(tmp_path):
    outdir = tmp_path.with_suffix(".vcfstats")
    outdir.mkdir(parents=True)
    return Instance(
        "AAF ~ CHROM",
        "title",
        "",
        {"width": 1000, "height": 1000, "res": 100},
        outdir,
        ["A", "B", "C", "D"],
        None,
        False,
    )


@pytest.mark.parametrize(
    "title,expected",
    [
        ("abc.d", "abc.d"),
        ("abc/d", "abc_d"),
    ],
)
def test_title_to_valid_path(title, expected):
    assert title_to_valid_path(title) == expected


@pytest.mark.parametrize(
    "formula,figtype,expected",
    [
        ("COUNT(1) ~ COUNT(1,group=CHROM)", None, "scatter"),
        ("COUNT(1) ~ COUNT(1,group=CHROM)", "pie", TypeError),
        ("COUNT(1) ~ CHROM", "bar", "col"),
        ("COUNT(1) ~ CHROM", "scatter", TypeError),
        ("VARTYPE ~ CHROM", None, "bar"),
        ("VARTYPE ~ CHROM", "scatter", TypeError),
        ("AAF ~ CHROM", None, "violin"),
        ("AAF ~ CHROM", "scatter", TypeError),
        ("CHROM ~ AAF", None, TypeError),
        ("VARTYPE ~ 1", None, "pie"),
        ("VARTYPE ~ 1", "boxplot", TypeError),
        ("QUAL ~ AAF", None, "scatter"),
        ("QUAL ~ AAF", "boxplot", TypeError),
        ("QUAL ~ 1", None, "histogram"),
        ("QUAL ~ 1", "scatter", TypeError),
    ],
)
def test_get_plot_type(formula, figtype, expected):
    fmula = Formula(formula, None, False, "title")
    if hasattr(expected, "__bases__") and Exception in expected.__bases__:
        with pytest.raises(expected):
            get_plot_type(fmula, figtype)
    else:
        assert get_plot_type(fmula, figtype) == expected


def test_one_init(tmp_path, instance):
    outdir = tmp_path.with_suffix(".vcfstats")
    outdir.mkdir(parents=True, exist_ok=True)
    assert instance.title == "title"
    assert instance.outprefix == str(
        outdir / title_to_valid_path(instance.title)
    )
    assert instance.devpars == {"width": 1000, "height": 1000, "res": 100}
    assert instance.ggs == ""
    assert not instance.datafile.closed

    instance = Instance(
        "COUNT(1, group=VARTYPE) ~ CHROM",
        "title",
        "",
        {"width": 1000, "height": 1000, "res": 100},
        outdir,
        ["A", "B", "C", "D"],
        None,
        False,
    )
    instance.datafile.close()
    assert (
        Path(instance.outprefix + ".txt").read_text()
        == "COUNT(_ONE)\tCHROM\tGroup\n"
    )


def test_one_iterate(tmp_path):
    outdir = tmp_path.with_suffix(".vcfstats")
    outdir.mkdir(parents=True)
    instance = Instance(
        "AAF ~ CHROM",
        "title",
        "",
        {"width": 1000, "height": 1000, "res": 100},
        outdir,
        ["A", "B", "C", "D"],
        None,
        False,
    )
    with pytest.raises(AttributeError):
        instance.iterate(None)


def test_summarize(instance):
    instance.summarize()
    assert instance.datafile.closed


def test_plot(instance, caplog):
    import logging

    with caplog.at_level(logging.INFO):
        instance.plot("Rscript")
    assert "no lines available in input" in caplog.text
