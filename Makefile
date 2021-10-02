TARGETS :=  examples/Number_of_variants_on_each_chromosome.col.png \
			examples/Number_of_variants_on_each_chromosome_(modified).col.png \
			examples/Number_of_variants_on_each_chromosome_(first_5).col.png \
			examples/Number_of_substitutions_of_SNPs.col.png \
			examples/Number_of_substitutions_of_SNPs_(passed).col.png \
			examples/Allele_frequency_on_each_chromosome.violin.png \
			examples/Allele_frequency_on_each_chromosome.boxplot.png \
			examples/Allele_frequency_on_chromosome_1_2.density.png \
			examples/Overall_allele_frequency_distribution.histogram.png \
			examples/Overall_allele_frequency_distribution_(0.05-0.95).histogram.png \
			examples/Distribution_of_allele_frequency_on_chromosome_1.histogram.png \
			examples/Types_of_variants_on_each_chromosome.col.png \
			examples/Types_of_variants_on_each_chromosome_1.pie.png \
			examples/Types_of_variants_on_whole_genome.pie.png \
			examples/Mutant_genotypes_on_each_chromosome_(sample_1).col.png \
			examples/GQ_vs_depth_(sample_1).scatter.png \
			examples/Depths_between_sample_1_and_2.scatter.png


DEPENDS :=  examples/sample.vcf examples/config.toml vcfstats/__init__.py \
			vcfstats/formula.py vcfstats/macros.py vcfstats/instance.py

VCFSTATS := vcfstats --vcf examples/sample.vcf \
	--outdir examples/ \
	--config examples/config.toml

FILETOTITLE = $(subst _, ,$(notdir $(basename $(basename $(1)))))
FIGTYPE = $(patsubst .%,%,$(suffix $(basename $(notdir $(1)))))
LOGGER = $(info $(empty))$(info \# Working on '$(call FILETOTITLE,$(1))' ...)\
		 $(info ===================================================================================)

.PHONY: all clean

all: $(TARGETS)

examples/Types_of_variants_on_whole_genome.col.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \


examples/Number_of_variants_on_each_chromosome.col.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'COUNT(1) ~ CONTIG'


examples/Number_of_variants_on_each_chromosome_(modified).col.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'COUNT(1) ~ CONTIG' \
	--ggs 'scale_x_discrete(name ="Chromosome", limits=["1","2","3","4","5","6","7","8","9","10","X"]); ylab("# Variants")'


examples/Number_of_substitutions_of_SNPs.col.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'COUNT(1, VARTYPE[snp]) ~ SUBST[A>T,A>G,A>C,T>A,T>G,T>C,G>A,G>T,G>C,C>A,C>T,C>G]' \

examples/Number_of_substitutions_of_SNPs_(passed).col.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'COUNT(1, VARTYPE[snp]) ~ SUBST[A>T,A>G,A>C,T>A,T>G,T>C,G>A,G>T,G>C,C>A,C>T,C>G]' \
	--passed

examples/Number_of_variants_on_each_chromosome_(first_5).col.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'COUNT(1) ~ CONTIG[1-5]'

examples/Allele_frequency_on_each_chromosome.violin.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'AAF ~ CONTIG' \
	--ggs 'theme_dark()'

examples/Allele_frequency_on_each_chromosome.boxplot.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'AAF ~ CONTIG'

examples/Allele_frequency_on_chromosome_1_2.density.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'AAF ~ CONTIG[1,2]' \
	--figtype density

examples/Overall_allele_frequency_distribution.histogram.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'AAF ~ 1'

examples/Overall_allele_frequency_distribution_(0.05-0.95).histogram.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'AAF[0.05, 0.95] ~ 1'

examples/Distribution_of_allele_frequency_on_chromosome_1.histogram.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'AAF ~ CHROM[1]'

examples/Types_of_variants_on_each_chromosome.col.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'COUNT(1, group=VARTYPE) ~ CHROM'

examples/Types_of_variants_on_each_chromosome_1.pie.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'COUNT(1, group=VARTYPE) ~ CHROM[1]' \
	--figtype pie

examples/Types_of_variants_on_whole_genome.pie.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'COUNT(1, group=VARTYPE) ~ 1'

examples/GQ_vs_depth_(sample_1).scatter.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'MEAN(GQs{0}) ~ MEAN(DEPTHs{0}, group=CHROM)'

examples/Mutant_genotypes_on_each_chromosome_(sample_1).col.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'COUNT(1, group=GTTYPEs[HET,HOM_ALT]{0}) ~ CHROM'

examples/Depths_between_sample_1_and_2.scatter.png: $(DEPENDS)
	@$(call LOGGER,$@)
	$(VCFSTATS) --title '$(call FILETOTITLE,$@)' --figtype $(call FIGTYPE,$@) \
	--formula 'DEPTHs{0} ~ DEPTHs{1}'

clean:
	rm -f examples/*.csv examples/*.png
