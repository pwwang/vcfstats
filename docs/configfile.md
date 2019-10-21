# Configuration file

We are using `toml` file as configuration file. Please refer to its [documentation](https://github.com/toml-lang/toml).

To overwrite arguments from command line, just specify the values directly in the configuration file. For example:
```toml
devpars = {width = 1000, height = 1000, res = 100}
passed = true
```

To specify multiple plots, we do:
```toml
passed = true

[[one]]
formula = 'DEPTHs{0} ~ CHROM'
title = 'Depth distribution on each chromosome'
ggs = 'theme_minimal()'
devpars = {width = 1000, height = 1000, res = 100}

[[one]]
formula = 'AAF ~ CHROM'
title = 'Allele frequency distribution on each chromosome'
ggs = 'theme_bw()'
devpars = {width = 2000, height = 2000, res = 300}

```
