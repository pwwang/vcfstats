
vcfstats - powerful statistics for VCF files
============================================

`
.. image:: https://img.shields.io/pypi/v/vcfstats?style=flat-square
   :target: https://img.shields.io/pypi/v/vcfstats?style=flat-square
   :alt: Pypi
 <https://pypi.org/project/vcfstats/>`_ `
.. image:: https://img.shields.io/github/v/tag/pwwang/vcfstats?style=flat-square
   :target: https://img.shields.io/github/v/tag/pwwang/vcfstats?style=flat-square
   :alt: Github
 <https://github.com/pwwang/vcfstats>`_ `
.. image:: https://img.shields.io/pypi/pyversions/vcfstats?style=flat-square
   :target: https://img.shields.io/pypi/pyversions/vcfstats?style=flat-square
   :alt: PythonVers
 <https://pypi.org/project/vcfstats/>`_ `
.. image:: https://img.shields.io/readthedocs/vcfstats?style=flat-square
   :target: https://img.shields.io/readthedocs/vcfstats?style=flat-square
   :alt: docs
 <https://vcfstats.readthedocs.io/en/latest/>`_ `
.. image:: https://img.shields.io/travis/pwwang/vcfstats?style=flat-square
   :target: https://img.shields.io/travis/pwwang/vcfstats?style=flat-square
   :alt: Travis building
 <https://travis-ci.org/pwwang/vcfstats>`_ `
.. image:: https://img.shields.io/codacy/grade/76b84a4cba794f1d925ba98913203c05?style=flat-square
   :target: https://img.shields.io/codacy/grade/76b84a4cba794f1d925ba98913203c05?style=flat-square
   :alt: Codacy
 <https://app.codacy.com/manual/pwwang/vcfstats>`_ `
.. image:: https://img.shields.io/codacy/coverage/76b84a4cba794f1d925ba98913203c05?style=flat-square
   :target: https://img.shields.io/codacy/coverage/76b84a4cba794f1d925ba98913203c05?style=flat-square
   :alt: Codacy coverage
 <https://app.codacy.com/manual/pwwang/vcfstats>`_

`Documentation <https://vcfstats.readthedocs.io/en/latest/>`_ | `CHANGELOG <https://vcfstats.readthedocs.io/en/latest/CHANGELOG/>`_

Motivation
----------

There are a couple of tools that can plot some statistics of VCF files, including `\ ``bcftools`` <https://samtools.github.io/bcftools/bcftools.html#stats>`_ and `\ ``jvarkit`` <http://lindenb.github.io/jvarkit/VcfStatsJfx.html>`_. However, none of them could:


#. plot specific metrics
#. customize the plots
#. focus on variants with certain filters

R package `\ ``vcfR`` <https://knausb.github.io/vcfR_documentation/visualization_1.html>`_ can do some of the above. However, it has to load entire VCF into memory, which is not friendly to large VCF files.

Installation
------------

``vcfstats`` also requires `\ ``R`` <https://www.r-project.org/>`_ with `\ ``ggplot2`` <https://ggplot2.tidyverse.org/>`_ to be installed. \
If you are doing ``pie`` chart, `\ ``ggrepel`` <https://cran.r-project.org/web/packages/ggrepel/vignettes/ggrepel.html>`_ is also required.

.. code-block:: shell

   pip install vcfstats

Gallery
-------

Number of variants on each chromosome
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'COUNT(1) ~ CONTIG' \
       --title 'Number of variants on each chromosome' \
       --config examples/config.toml


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_variants_on_each_chromosome.col.png
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_variants_on_each_chromosome.col.png
   :alt: Number of variants on each chromosome


Changing labels and ticks
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'COUNT(1) ~ CONTIG' \
       --title 'Number of variants on each chromosome (modified)' \
       --config examples/config.toml \
       --ggs 'scale_x_discrete(name ="Chromosome", \
           limits=c("1","2","3","4","5","6","7","8","9","10","X")) + \
           ylab("# Variants")'


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_variants_on_each_chromosome_(modified
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_variants_on_each_chromosome_(modified
   :alt: Number of variants on each chromosome (modified)
.col.png)

Number of variants on first 5 chromosome
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

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


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_variants_on_each_chromosome_(first_5
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_variants_on_each_chromosome_(first_5
   :alt: Number of variants on each chromosome (first 5)
.col.png)

Number of substitutions of SNPs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'COUNT(1, VARTYPE[snp]) ~ SUBST[A>T,A>G,A>C,T>A,T>G,T>C,G>A,G>T,G>C,C>A,C>T,C>G]' \
       --title 'Number of substitutions of SNPs' \
       --config examples/config.toml


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_substitutions_of_SNPs.col.png
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_substitutions_of_SNPs.col.png
   :alt: Number of substitutions of SNPs


Only with SNPs PASS all filters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'COUNT(1, VARTYPE[snp]) ~ SUBST[A>T,A>G,A>C,T>A,T>G,T>C,G>A,G>T,G>C,C>A,C>T,C>G]' \
       --title 'Number of substitutions of SNPs (passed)' \
       --config examples/config.toml \
       --passed


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_substitutions_of_SNPs_(passed
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Number_of_substitutions_of_SNPs_(passed
   :alt: Number of substitutions of SNPs (passed)
.col.png)

Alternative allele frequency on each chromosome
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

   # using a dark theme
   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'AAF ~ CONTIG' \
       --title 'Allele frequency on each chromosome' \
       --config examples/config.toml --ggs 'theme_dark()'


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Allele_frequency_on_each_chromosome.violin.png
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Allele_frequency_on_each_chromosome.violin.png
   :alt: Allele frequency on each chromosome


Using boxplot
~~~~~~~~~~~~~

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'AAF ~ CONTIG' \
       --title 'Allele frequency on each chromosome (boxplot)' \
       --config examples/config.toml \
       --figtype boxplot


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Allele_frequency_on_each_chromosome.boxplot.png
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Allele_frequency_on_each_chromosome.boxplot.png
   :alt: Allele frequency on each chromosome


Using density plot/histogram to investigate the distribution:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can plot the distribution, using density plot or histogram

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'AAF ~ CONTIG[1,2]' \
       --title 'Allele frequency on chromosome 1,2' \
       --config examples/config.toml \
       --figtype density


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Allele_frequency_on_chromosome_1_2.density.png
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Allele_frequency_on_chromosome_1_2.density.png
   :alt: Allele frequency on chromosome 1,2


Overall distribution of allele frequency
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'AAF ~ 1' \
       --title 'Overall allele frequency distribution' \
       --config examples/config.toml


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Overall_allele_frequency_distribution.histogram.png
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Overall_allele_frequency_distribution.histogram.png
   :alt: Overall allele frequency distribution


Excluding some low/high frequency variants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'AAF[0.05, 0.95] ~ 1' \
       --title 'Overall allele frequency distribution (0.05-0.95)' \
       --config examples/config.toml


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Overall_allele_frequency_distribution_(0.05-0.95
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Overall_allele_frequency_distribution_(0.05-0.95
   :alt: Overall allele frequency distribution
.histogram.png)

Counting types of variants on each chromosome
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'COUNT(1, group=VARTYPE) ~ CHROM' \
       # or simply
       # --formula 'VARTYPE ~ CHROM' \
       --title 'Types of variants on each chromosome' \
       --config examples/config.toml


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Types_of_variants_on_each_chromosome.col.png
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Types_of_variants_on_each_chromosome.col.png
   :alt: Types of variants on each chromosome


Using pie chart if there is only one chromosome
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'COUNT(1, group=VARTYPE) ~ CHROM[1]' \
       # or simply
       # --formula 'VARTYPE ~ CHROM[1]' \
       --title 'Types of variants on each chromosome 1' \
       --config examples/config.toml \
       --figtype pie


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Types_of_variants_on_each_chromosome_1.pie.png
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Types_of_variants_on_each_chromosome_1.pie.png
   :alt: Types of variants on each chromosome 1


Counting variant types on whole genome
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       # or simply
       # --formula 'VARTYPE ~ 1' \
       --formula 'COUNT(1, group=VARTYPE) ~ 1' \
       --title 'Types of variants on whole genome' \
       --config examples/config.toml


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Types_of_variants_on_whole_genome.pie.png
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Types_of_variants_on_whole_genome.pie.png
   :alt: Types of variants on whole genome


Counting type of mutant genotypes (HET, HOM_ALT) for sample 1 on each chromosome
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       # or simply
       # --formula 'GTTYPEs[HET,HOM_ALT]{0} ~ CHROM' \
       --formula 'COUNT(1, group=GTTYPEs[HET,HOM_ALT]{0}) ~ CHROM' \
       --title 'Mutant genotypes on each chromosome (sample 1)' \
       --config examples/config.toml


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Mutant_genotypes_on_each_chromosome_(sample_1
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Mutant_genotypes_on_each_chromosome_(sample_1
   :alt: Mutant genotypes on each chromosome
.col.png)

Exploration of mean(genotype quality) and mean(depth) on each chromosome for sample 1
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'MEAN(GQs{0}) ~ MEAN(DEPTHs{0}, group=CHROM)' \
       --title 'GQ vs depth (sample 1)' \
       --config examples/config.toml


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/GQ_vs_depth_(sample_1
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/GQ_vs_depth_(sample_1
   :alt: GQ vs depth (sample 1)
.scatter.png)

Exploration of depths for sample 1,2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

   vcfstats --vcf examples/sample.vcf \
       --outdir examples/ \
       --formula 'DEPTHs{0} ~ DEPTHs{1}' \
       --title 'Depths between sample 1 and 2' \
       --config examples/config.toml


.. image:: https://github.com/pwwang/vcfstats/raw/master/examples/Depths_between_sample_1_and_2.scatter.png
   :target: https://github.com/pwwang/vcfstats/raw/master/examples/Depths_between_sample_1_and_2.scatter.png
   :alt: Depths between sample 1 and 2

