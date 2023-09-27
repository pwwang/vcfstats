# Macros

Macros are used to gather some information from variants. They are nothing but just python function with our decorators.

To define a macro:

```python
from vcfstats.macros import continuous

@continuous
def QUAL(variant):
	return variant.QUAL
```

We are using `cyvcf2` to get variant information, please refer to its [API documentation](https://brentp.github.io/cyvcf2/docstrings.html) to explore what kind of metrics we can get from a variant.

!!! note

	`vcf` is initialized with `gts012 = True`, which is not the default value of `cyvcf2`. \
	`gts012 = True` indicates that genotype 2 as `HOM_ALT` and 3 as `UNKNOWN`.


## Shortcuts for macro decorators

|decrator|shortcut|
|-|-|
|continuous|cont|
|categorical|cat|
|aggregation|aggr|

## Macros other than aggregations with sample data

If a macro returns sample data, we need to return a list or `numpy.array` with data for each sample. In the formula, we have to use brackets to get the information of certain sample. For example:

```python
from vcf.macros import cat

@cat
def GTTYPEs(variant)
	gttypes = variant.gt_types
	return ['HOM_REF'if gttype == 0 else \
			'HET' if gttype == 1 else \
			'HOM_ALT' if gttype == 2 else 'UNKNOWN' for gttype in gttypes]
```

To get the genotype in sample 1 in formula: `GTTYPEs{0}`. You can also use sample name as well: `GTTYPEs{some sample}`

It's also allowed to pass `vcf` (the instance of `cyvcf.VCF`) as the second argument to the macro. For example:

```python
from vcf.macros import cont

@cont
def MIXED_INFO(variant, vcf):
	...
```

Check the [API documentation](https://brentp.github.io/cyvcf2/docstrings.html) of `cyvcf2` to see what information we can get from `vcf`.


## Macros with filters

`aggregation`s have different syntax for filters. Here we are discussing about `continuous` and `categorical`.

For `continuous` macros, we can use an upper and lower bound to filter. For example: `AAF[0.05, 0.95]` will take only variants with alternate allele frequency within `[0.05, 0.95]`, including `0.05` and `0.95`. We don't have a lower/upper bound exclusive syntax, so to exclude `0.05`, we can specify some value less than and close to it, say `0.0499`.

For `categorical` macros, we can specify the categories that we want to keep in the plotting. For example: `CHROM[chr1, chr2, chr3]`. More conveniently, we can use hyphen to include a range of categories. For example, `CHROM[chr1-chr22, chrX, chrY]` will include all human chromosomes.

!!! hint

	With both filters and sample subscribes, it doesn't matter which one you put it first. That means you can do both `GTTYPEs{0}[HET]` and `GTTYPEs[HET]{0}`. They are the same.

## Aggregations

When you define aggregations, you just define who to aggregate the values. For example:
```python
from vcfstats.macros import aggr
@aggr
def SUM(values):
	return sum(values)
```
While when you use it, you can specify macros as filter and group for it. For example: `SUM(DEPTHs{0}, filter=FILTER[PASS], group=CHROM)`. This means to sum up the depth of variants pass all filters on each chromosome for the first sample.

!!! note

	Generally, we have to specify `group` for an aggregation. There are 2 situations that you don't have to:

	1. when an aggregation is used as `Y`, left part of the formula, and `X` is a categorical macro. Then the categorical values will be used as `group` for the aggregation.

	2. both `X` and `Y` are aggregations and one of them can have no `group` and will use the `group` from the other one.

## Built-in macros
```python


@categorical
def VARTYPE(variant):
	"""Variant type, one of deletion, indel, snp or sv"""
	return 	variant.var_type

@categorical
def TITV(variant):
	"""Tell if a variant is a transition or transversion. The variant has to be an snp first."""
	if not variant.is_snp:
		return False
	return 'transition' if variant.is_transition else 'transversion'

@categorical(alias = 'CHROM')
def CONTIG(variant):
	"""Get the config/chromosome of a variant. Alias: CHROM"""
	return variant.CHROM

@categorical(alias = 'GT_TYPEs')
def GTTYPEs(variant):
	"""Get the genotypes(HOM_REF,HET,HOM_ALT,UNKNOWN) of a variant for each sample"""
	gttypes = variant.gt_types
	return ['HOM_REF'if gttype == 0 else \
			'HET' if gttype == 1 else \
			'HOM_ALT' if gttype == 2 else 'UNKNOWN' for gttype in gttypes]

@categorical
def FILTER(variant):
	"""Get the FILTER of a variant."""
	return variant.FILTER or 'PASS'

@categorical
def SUBST(variant):
	"""Substitution of the variant, including all types of varinat"""
	return '{}>{}'.format(variant.REF, ','.join(variant.ALT))

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

@continuous(alias = 'DPs')
def DEPTHs(variant):
	"""Get the read-depth for each sample as a numpy array."""
	return [sum(dp) for dp in variant.format('DP')]

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
	"""Return 1 for a variant, usually used in aggregation, or indication of a distribution plot"""
	return 1

@aggregation
def COUNT(entries):
	"""Count the variants in groups"""
	return len(entries)

@aggregation
def SUM(entries):
	"""Sum up the values in groups"""
	return sum(entries)

@aggregation(alias = 'AVG')
def MEAN(entries):
	"""Get the mean of the values"""
	if not entries:
		return 0.0
	return sum(entries) / len(entries)
```
