# Formulas

Formulas are composed of macros on both sides, which are connected by `'~'`. It looks like the formula syntax from `R`: `Y ~ X`. This basically determines how the plots are generated.

However, we don't support operators like it from `R`. So we only have `Y ~ X`, but not `Y ~ X1 + X2`. In order to implement this, we have to define a macro to add `X1` and `X2` up.

We have three types of macros:
1. `continuous`: extracts continues values from a variant, such as allele frequency, depth, etc.
2. `categorical`: extracts categorical values from a variant, such as variant type, genotype, etc.
3. `aggregation`: aggregates some values from a group of variants, such as mean of allele frequency from chromosome 1

See section `Macros` for details.

## Predefined figure types for different combination of `Y` and `X`

|Y|X|default figure type|other available figure types|
|-|-|-|-|
|`aggregation`|`aggregation`|scatter|-|
|`aggregation`|`categorical`|col|pie|
|`aggregation`|`1`|pie|col|
|anything other than `aggregation`|`aggregation`|not available|-|
|`categorical`|`categorical`|bar|-|
|`continuous`|`categorical`|voilin|boxplot/histogram/density/freqpoly|
|`categorical`|`continuous`|not available|-|
|`continueous`|`continuous`|scatter|-|

## `geom`s from `ggplot2` used to plot for different figure types

|figure type|geom|
|-|-|
|scatter|`geom_point`|
|col|`geom_col`|
|pie|`geom_col` with `coord_polar`|
|bar|`geom_bar`|
|violin|`geom_violin`|
|boxplot|`geom_boxplot`|
|density|`geom_density`|
|freqpoly|`geom_freqpoly`|

