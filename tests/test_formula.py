import pytest
from io import StringIO
from pathlib import Path
from cyvcf2 import VCF
from vcfstats import MACROS
from vcfstats.macros import cat
from vcfstats.formula import parse_subsets, Term, Aggr, Formula, safe_split

HERE = Path(__file__).parent.resolve()

@pytest.fixture(scope = "module")
def variants():
	vcf = VCF(str(HERE.parent.joinpath('examples', 'sample.vcf')), gts012 = True)
	return list(vcf)

@cat
def FILTER2(variant):
	return variant.FILTER

@pytest.mark.parametrize('subsets,expected', [
	('a,b,c', ['a', 'b', 'c']),
	('a, b, c', ['a', 'b', 'c']),
	('1-8,12', ['1', '2', '3', '4', '5', '6', '7','8','12']),
	('chr1-chr10, a-b', ['chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9', 'chr10', 'a-b']),
])
def test_parse_subsets(subsets, expected):
	assert parse_subsets(subsets) == expected

@pytest.mark.parametrize('string, delimit, trim, expect', [
	("a\"|\"b", "|", True, ["a\"|\"b"]),
	("a|b|c", "|", True, ["a", "b", "c"]),
	('a|b\\|c', "|", True, ["a", "b\\|c"]),
	('a|b\\|c|(|)', "|", True, ["a", "b\\|c", "(|)"]),
	('a|b\\|c|(\\)|)', "|", True, ["a", "b\\|c", "(\\)|)"]),
	('a|b\\|c|(\\)\\\'|)', "|", True, ["a", "b\\|c", "(\\)\\'|)"]),
	('a|b\\|c |(\\)\\\'|)', "|", False, ["a", "b\\|c ", "(\\)\\'|)"]),
	('outdir:dir:{{i.pattern | lambda x: __import__("glob").glob(x)[0] | fn }}_etc', ':', True, ["outdir", "dir", "{{i.pattern | lambda x: __import__(\"glob\").glob(x)[0] | fn }}_etc"]),
])
def test_safe_split(string, delimit, trim, expect):
	assert safe_split(string, delimit, trim) == expect

def test_term_init():
	term = Term('AAF', None)
	assert term.name == 'AAF'
	assert term.term == MACROS['AAF']
	assert term.samples == None
	assert term.subsets == None

	term = Term('AAF[.05, .95]', None)
	assert term.subsets == [.05, .95]

	term = Term('1', None)
	assert term.name == '1'

	with pytest.raises(ValueError):
		Term('NoSuchTerm', None)

	MACROS['NOTYPE'] = {}
	with pytest.raises(TypeError):
		Term('NOTYPE', None)
	del MACROS['NOTYPE']

	term = Term('AFs{1}', ['sample1', 'sample2'])
	assert term.samples == [1]

	with pytest.raises(ValueError):
		Term('AFs{sample2][,0.5]', ['sample1', 'sample2'])

	term = Term('AFs{sample2}[,0.5]', ['sample1', 'sample2'])
	assert term.samples == [1]
	assert term.subsets == ['', 0.5]

	with pytest.raises(ValueError):
		Term('AFs[sample2}{,0.5}', ['sample1', 'sample2'])

	term2 = Term('AFs[,.5]{sample2}', ['sample1', 'sample2'])
	assert term2.samples == [1]
	assert term2.subsets == ['', 0.5]
	assert repr(term2) == "<Term AFs(subsets=['', 0.5], samples=[1])>"
	assert term2 == term
	assert term2 != 1

	with pytest.raises(ValueError):
		Term('AFs[)', None)

	with pytest.raises(ValueError):
		Term('AFs{sample}', ['sample1', 'sample2'])

	with pytest.raises(KeyError):
		Term('AFs[1,2,3]', None)

def test_term_run(variants):
	term = Term('FILTER[PASS]', None)
	assert term.run(variants[0], passed = True) == False
	assert term.run(variants[5], passed = True) == ['PASS']

	term = Term('FILTER2', None)
	assert term.run(variants[5], passed = True) == False

	term = Term('GTTYPEs{0}', ['A', 'B', 'C', 'D'])
	assert term.run(variants[0], passed = False) == ['HOM_REF']

	term = Term('AAF[.126,]', None)
	# .125
	assert term.run(variants[0], passed = False) == False
	assert term.run(variants[2], passed = False) == [.25]
	term = Term('AAF[,.24]', None)
	# .25
	assert term.run(variants[0], passed = False) == [.125]
	assert term.run(variants[2], passed = False) == False

	term = Term('FILTER[PASS]', None)
	assert term.run(variants[0], passed = False) == False
	assert term.run(variants[5], passed = False) == ['PASS']

def test_aggr_init():
	with pytest.raises(ValueError):
		Aggr('COUNT', {})
	with pytest.raises(ValueError):
		Aggr('COUNT(', {})
	with pytest.raises(ValueError):
		Aggr('NoSuchAggr()', {})
	aggr = Aggr('COUNT(1)', {'1': Term('1', None)})
	assert aggr.term == Term('1', None)
	assert aggr.filter is None
	assert aggr.group is None
	assert not aggr.hasFILTER()

	aggr = Aggr('COUNT(1, FILTER[PASS])', {'1': Term('1', None), 'FILTER[PASS]': Term('FILTER[PASS]', None)})
	assert aggr.term == Term('1', None)
	assert aggr.filter == Term('FILTER[PASS]', None)
	assert aggr.group is None

	aggr = Aggr('COUNT(1, filter = FILTER[PASS])', {'1': Term('1', None), 'FILTER[PASS]': Term('FILTER[PASS]', None)})
	assert aggr.term == Term('1', None)
	assert aggr.filter == Term('FILTER[PASS]', None)
	assert aggr.group is None
	assert aggr.hasFILTER()
	aggr.setxgroup(Term('VARTYPE', None))
	assert aggr.group == Term('VARTYPE', None)
	assert aggr.xgroup is None

	aggr = Aggr('COUNT(1, filter = FILTER[PASS], group = VARTYPE)', {'1': Term('1', None), 'FILTER[PASS]': Term('FILTER[PASS]', None), 'VARTYPE': Term('VARTYPE', None)})
	assert aggr.term == Term('1', None)
	assert aggr.filter == Term('FILTER[PASS]', None)
	assert aggr.group == Term('VARTYPE', None)
	assert aggr.xgroup is None
	aggr.setxgroup(Term('GTTYPEs{0}', ['A']))
	assert aggr.xgroup == Term('GTTYPEs{0}', ['A'])
	assert repr(aggr) == "<Aggr COUNT(<Term 1(subsets=None, samples=None)>, filter=<Term FILTER(subsets=['PASS'], samples=None)>, group=<Term VARTYPE(subsets=None, samples=None)>)>"
	assert aggr.hasFILTER()

	aggr = Aggr('COUNT(1, FILTER, VARTYPE)', {'1': Term('1', None), 'FILTER': Term('FILTER', None), 'VARTYPE': Term('VARTYPE', None)})
	assert aggr.term == Term('1', None)
	assert aggr.filter == Term('FILTER', None)
	assert aggr.group == Term('VARTYPE', None)

	aggr = Aggr('COUNT(1, GTTYPEs)', {'1': Term('1', None), 'GTTYPEs': Term('GTTYPEs', None)})
	assert aggr.term == Term('1', None)
	assert aggr.filter == Term('GTTYPEs', None)
	assert aggr.group == None

	with pytest.raises(TypeError):
		Aggr('COUNT(FILTER)', {'FILTER': Term('FILTER', None)})

	with pytest.raises(TypeError):
		Aggr('COUNT(1, group = AAF)', {'AAF': Term('AAF', None), '1': Term('1', None)})

def test_aggr_run(variants):
	aggr = Aggr('COUNT(1, filter = FILTER[PASS], group = VARTYPE)', {'1': Term('1', None), 'FILTER[PASS]': Term('FILTER[PASS]', None), 'VARTYPE': Term('VARTYPE', None)})
	aggr.run(variants[0], passed = True)
	assert len(aggr.cache) == 0

	aggr2 = Aggr('COUNT(1, filter = FILTER[PASS])', {'1': Term('1', None), 'FILTER[PASS]': Term('FILTER[PASS]', None), 'VARTYPE': Term('VARTYPE', None)})
	with pytest.raises(RuntimeError):
		aggr2.run(variants[5], passed = True)

	aggr3 = Aggr('COUNT(1, filter = FILTER[PASS], group = FILTER2)', {'1': Term('1', None), 'FILTER[PASS]': Term('FILTER[PASS]', None), 'FILTER2': Term('FILTER2', None)})
	aggr3.run(variants[5], passed = False)
	assert len(aggr3.cache) == 0

	aggr4 = Aggr('COUNT(1, group = GTTYPEs)', {'1': Term('1', None), 'GTTYPEs': Term('GTTYPEs', None)})
	with pytest.raises(ValueError):
		aggr4.run(variants[0], passed = False)

	aggr5 = Aggr('COUNT(1, group = VARTYPE)', {'1': Term('1', None), 'VARTYPE': Term('VARTYPE', None)})
	aggr5.run(variants[0], passed = False)
	assert aggr5.cache == {'snp': [1]}
	aggr5.run(variants[1], passed = False)
	assert aggr5.cache == {'snp': [1,1]}
	aggr5.run(variants[3], passed = False)
	assert aggr5.cache == {'snp': [1,1], 'indel': [1]}

	assert aggr5.dump() == {'snp': 2, 'indel': 1}

	aggr5.cache.clear()
	aggr5.setxgroup(Term('FILTER', None))
	aggr5.run(variants[0], passed = False)
	assert aggr5.cache == {'MinMQ': {'snp': [1]}}

	aggr5.cache.clear()
	aggr5.setxgroup(Term('FILTER2', None))
	aggr5.run(variants[0], passed = False)
	assert aggr5.cache == {'MinMQ': {'snp': [1]}}
	aggr5.run(variants[5], passed = False)
	assert aggr5.cache == {'MinMQ': {'snp': [1]}}
	aggr5.run(variants[1], passed = False)
	assert aggr5.cache == {'MinMQ': {'snp': [1,1]}}
	assert aggr5.dump() == {'MinMQ': [(2, 'snp')]}

	aggr5.setxgroup(Term('GTTYPEs', ['A', 'B', 'C', 'D']))
	with pytest.raises(ValueError):
		aggr5.run(variants[0], passed = False)

	aggr6 = Aggr('MEAN(AAF[.2,], group = CHROM)', {'AAF[.2,]': Term('AAF[.2,]', None), 'CHROM': Term('CHROM', None)})
	aggr6.run(variants[0], passed = False) # .125
	assert len(aggr6.cache) == 0

def test_formula_init():
	fmula = Formula('AAF', None, False, 'title')
	assert fmula.Y == Term('AAF', None)
	assert fmula.X == Term('1', None)
	assert fmula._terms == {}

	fmula = Formula('AAF~', None, False, 'title')
	assert fmula.Y == Term('AAF', None)
	assert fmula.X == Term('1', None)
	assert fmula._terms == {}

	fmula = Formula('MEAN(AAF) ~ CHROM', None, True, 'title')
	assert fmula.Y.group == Term('CHROM', None)
	assert fmula._terms == {'TERM0': Term('AAF', None)}
	assert fmula.passed

	fmula = Formula('MEAN(AAF) ~ FILTER', None, True, 'title')
	assert not fmula.passed

	with pytest.raises(ValueError):
		Formula('MEAN(AAF, FILTER, CHROM, VARTYPE) ~ FILTER', None, True, 'title')

	fmula = Formula('MEAN(AAF, FILTER[PASS], group=VARTYPE) ~ CHROM', None, True, 'title')
	assert isinstance(fmula.Y, Aggr)
	assert isinstance(fmula.X, Term)

	with pytest.raises(ValueError):
		Formula('MEAN(AAF, FILTER[PASS], group1=VARTYPE) ~ CHROM', None, True, 'title')

def test_formula_run(variants):
	datafile = StringIO()
	fmula = Formula('AFs{0,1} ~ GTTYPEs{0-2}', None, False, 'title')
	with pytest.raises(RuntimeError):
		fmula.run(variants[0], datafile)

	fmula = Formula('FILTER2 ~ CHROM', None, False, 'title')
	fmula.run(variants[5], datafile)
	assert datafile.getvalue() == ''

	fmula = Formula('GTTYPEs ~ CHROM', None, False, 'title')
	fmula.run(variants[0], datafile)
	assert datafile.getvalue() == 'HOM_REF\t1\nHOM_REF\t1\nHOM_REF\t1\nHET\t1\n'

	datafile.truncate(0)
	datafile.seek(0)
	fmula = Formula('CHROM ~ GTTYPEs', None, False, 'title')
	fmula.run(variants[0], datafile)
	assert datafile.getvalue() == '1\tHOM_REF\n1\tHOM_REF\n1\tHOM_REF\n1\tHET\n'

	datafile.truncate(0)
	datafile.seek(0)
	fmula = Formula('COUNT(1, VARTYPE, CHROM) ~ COUNT(1, GTTYPEs)', None, False, 'title')
	fmula.run(variants[0], datafile)
	fmula.run(variants[1], datafile)
	assert datafile.getvalue() == ''
	fmula.done(datafile)
	assert datafile.getvalue() == '2\t2\t1\n'

	datafile.truncate(0)
	datafile.seek(0)
	fmula = Formula('COUNT(1, VARTYPE) ~ COUNT(1, GTTYPEs, CHROM)', None, False, 'title')
	fmula.run(variants[0], datafile)
	assert datafile.getvalue() == ''

	with pytest.raises(ValueError):
		Formula('COUNT(1, VARTYPE, GTTYPEs{0}) ~ COUNT(1, GTTYPEs, CHROM)', ['A', 'B', 'C', 'D'], False, 'title')

	fmula = Formula('COUNT(1) ~ CHROM', None, False, 'title')
	fmula.run(variants[0], datafile)
	fmula.run(variants[1], datafile)
	assert datafile.getvalue() == ''
	assert fmula.Y.cache == {'1': [1,1]}
	fmula.done(datafile)
	assert datafile.getvalue() == '2\t1\n'

	fmula = Formula('CHROM ~ COUNT(1)', None, False, 'title')
	with pytest.raises(TypeError):
		fmula.run(variants[0], datafile)

	datafile.truncate(0)
	datafile.seek(0)
	fmula = Formula('COUNT(1, group = VARTYPE) ~ CHROM', None, False, 'title')
	fmula.run(variants[0], datafile)
	fmula.run(variants[1], datafile)
	fmula.run(variants[2], datafile)
	fmula.run(variants[3], datafile)
	fmula.done(datafile)
	assert datafile.getvalue() == '3\t1\tsnp\n1\t1\tindel\n'

