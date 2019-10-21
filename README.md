# vcfstats - powerful statistics for VCF files

[![Pypi][1]][2] [![Github][3]][4] [![PythonVers][5]][2] [![docs][6]][13] [![Travis building][7]][8] [![Codacy][9]][10] [![Codacy coverage][11]][10]

[Documentation][13] | [CHANGELOG][12]

## Motivation
There are a couple of tools that can plot some statistics of VCF files, including [`bcftools`][14] and [`jvarkit`][15]. However, none of them could:
1. plot specific metrics
2. customize the plots
3. focus on variants with certain filters

R package [`vcfR`][19] can do some of the above. However, it has to load entire VCF into memory, which is not friendly to large VCF files.

## Installation
`vcfstats` also requires [`R`][16] with [`ggplot2`][17] to be installed. \
If you are doing `pie` chart, [`ggrepel`][18] is also required.
```shell
pip install vcfstats
```

## Gallery

### Number of variants on each chromosome

```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1) ~ CONTIG' \
	--title 'Number of variants on each chromosome' \
	--config examples/config.toml
```

![Number of variants on each chromosome](https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_variants_on_each_chromosome.col.png)

#### Changing labels and ticks

```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1) ~ CONTIG' \
	--title 'Number of variants on each chromosome (modified)' \
	--config examples/config.toml \
	--ggs 'scale_x_discrete(name ="Chromosome", \
		limits=c("1","2","3","4","5","6","7","8","9","10","X")) + \
		ylab("# Variants")'
```

![Number of variants on each chromosome (modified)](https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_variants_on_each_chromosome_(modified).col.png)

#### Number of variants on first 5 chromosome

```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1) ~ CONTIG[1,2,3,4,5]' \
	--title 'Number of variants on each chromosome (first 5)' \
	--config examples/config.toml
# or
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1) ~ CONTIG[1-5]' \
	--title 'Number of variants on each chromosome (first 5)' \
	--config examples/config.toml
# or
# require vcf file to be tabix-indexed.
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1) ~ CONTIG' \
	--title 'Number of variants on each chromosome (first 5)' \
	--config examples/config.toml -r 1 2 3 4 5
```

![Number of variants on each chromosome (first 5)](https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_variants_on_each_chromosome_(first_5).col.png)

### Number of substitutions of SNPs
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1, VARTYPE[snp]) ~ SUBST[A>T,A>G,A>C,T>A,T>G,T>C,G>A,G>T,G>C,C>A,C>T,C>G]' \
	--title 'Number of substitutions of SNPs' \
	--config examples/config.toml
```
![Number of substitutions of SNPs](https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_substitutions_of_SNPs.col.png)

#### Only with SNPs PASS all filters

```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1, VARTYPE[snp]) ~ SUBST[A>T,A>G,A>C,T>A,T>G,T>C,G>A,G>T,G>C,C>A,C>T,C>G]' \
	--title 'Number of substitutions of SNPs (passed)' \
	--config examples/config.toml \
	--passed
```

![Number of substitutions of SNPs (passed)](https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_substitutions_of_SNPs_(passed).col.png)

### Alternative allele frequency on each chromosome
```shell
# using a dark theme
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'AAF ~ CONTIG' \
	--title 'Allele frequency on each chromosome' \
	--config examples/config.toml --ggs 'theme_dark()'
```

![Allele frequency on each chromosome](https://github.com/pwwang/vcfstats/raw/master/examples/Allele_frequency_on_each_chromosome.violin.png)

#### Using boxplot
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'AAF ~ CONTIG' \
	--title 'Allele frequency on each chromosome (boxplot)' \
	--config examples/config.toml \
	--figtype boxplot
```

![Allele frequency on each chromosome](https://github.com/pwwang/vcfstats/raw/master/examples/Allele_frequency_on_each_chromosome.boxplot.png)

#### Using density plot/histogram to investigate the distribution:
You can plot the distribution, using density plot or histogram
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'AAF ~ CONTIG[1,2]' \
	--title 'Allele frequency on chromosome 1,2' \
	--config examples/config.toml \
	--figtype density
```
![Allele frequency on chromosome 1,2](https://github.com/pwwang/vcfstats/raw/master/examples/Allele_frequency_on_chromosome_1_2.density.png)

### Overall distribution of allele frequency
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'AAF ~ 1' \
	--title 'Overall allele frequency distribution' \
	--config examples/config.toml
```
![Overall allele frequency distribution](https://github.com/pwwang/vcfstats/raw/master/examples/Overall_allele_frequency_distribution.histogram.png)

#### Excluding some low/high frequency variants
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'AAF[0.05, 0.95] ~ 1' \
	--title 'Overall allele frequency distribution (0.05-0.95)' \
	--config examples/config.toml
```
![Overall allele frequency distribution](https://github.com/pwwang/vcfstats/raw/master/examples/Overall_allele_frequency_distribution_(0.05-0.95).histogram.png)

### Counting types of variants on each chromosome
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1, group=VARTYPE) ~ CHROM' \
	--title 'Types of variants on each chromosome' \
	--config examples/config.toml
```

![Types of variants on each chromosome](https://github.com/pwwang/vcfstats/raw/master/examples/Types_of_variants_on_each_chromosome.col.png)

#### Using pie chart if there is only one chromosome
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1, group=VARTYPE) ~ CHROM[1]' \
	--title 'Types of variants on each chromosome 1' \
	--config examples/config.toml \
	--figtype pie
```
![Types of variants on each chromosome 1](https://github.com/pwwang/vcfstats/raw/master/examples/Types_of_variants_on_each_chromosome_1.pie.png)

#### Counting variant types on whole genome
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1, group=VARTYPE) ~ 1' \
	--title 'Types of variants on whole genome' \
	--config examples/config.toml
```
![Types of variants on whole genome](https://github.com/pwwang/vcfstats/raw/master/examples/Types_of_variants_on_whole_genome.pie.png)

### Counting type of mutant genotypes (HET, HOM_ALT) for sample 1 on each chromosome
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'COUNT(1, group=GTTYPEs[HET,HOM_ALT]{0}) ~ CHROM' \
	--title 'Mutant genotypes on each chromosome (sample 1)' \
	--config examples/config.toml
```

![Mutant genotypes on each chromosome](https://github.com/pwwang/vcfstats/raw/master/examples/Mutant_genotypes_on_each_chromosome_(sample_1).col.png)


### Exploration of mean(genotype quality) and mean(depth) on each chromosome for sample 1
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'MEAN(GQs{0}) ~ MEAN(DEPTHs{0}, group=CHROM)' \
	--title 'GQ vs depth (sample 1)' \
	--config examples/config.toml
```
![GQ vs depth (sample 1)](https://github.com/pwwang/vcfstats/raw/master/examples/GQ_vs_depth_(sample_1).scatter.png)

### Exploration of depths for sample 1,2
```shell
vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--formula 'DEPTHs{0} ~ DEPTHs{1}' \
	--title 'Depths between sample 1 and 2' \
	--config examples/config.toml
```
![Depths between sample 1 and 2](https://github.com/pwwang/vcfstats/raw/master/examples/Depths_between_sample_1_and_2.scatter.png)

[1]: https://img.shields.io/pypi/v/vcfstats?style=flat-square
[2]: https://pypi.org/project/vcfstats/
[3]: https://img.shields.io/github/v/tag/pwwang/vcfstats?style=flat-square
[4]: https://github.com/pwwang/vcfstats
[5]: https://img.shields.io/pypi/pyversions/vcfstats?style=flat-square
[6]: https://img.shields.io/readthedocs/vcfstats?style=flat-square
[7]: https://img.shields.io/travis/pwwang/vcfstats?style=flat-square
[8]: https://travis-ci.org/pwwang/vcfstats
[9]: https://img.shields.io/codacy/grade/76b84a4cba794f1d925ba98913203c05?style=flat-square
[10]: https://app.codacy.com/manual/pwwang/vcfstats
[11]: https://img.shields.io/codacy/coverage/76b84a4cba794f1d925ba98913203c05?style=flat-square
[12]: https://vcfstats.readthedocs.io/en/latest/CHANGELOG/
[13]: https://vcfstats.readthedocs.io/en/latest/
[14]: https://samtools.github.io/bcftools/bcftools.html#stats
[15]: http://lindenb.github.io/jvarkit/VcfStatsJfx.html
[16]: https://www.r-project.org/
[17]: https://ggplot2.tidyverse.org/
[18]: https://cran.r-project.org/web/packages/ggrepel/vignettes/ggrepel.html
[19]: https://knausb.github.io/vcfR_documentation/visualization_1.html
