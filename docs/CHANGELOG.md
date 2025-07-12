# Change Log

## 0.7.0

- BREAKING: drop support for python3.8
- ci: use latest actions
- ci: update dependencies installation step to include tabix
- fix(tests): support bgzip < 1.20 (without -o option)

## 0.6.0

- ✨ Allow passing vcf as 2nd arg to macros (#45)
- ⬆️ Update dependencies

## 0.5.0

- ➕ Use argx instead of pyparam

## 0.4.3

- 🚑 Fix numpy error raised from plotnine (#35)
- 📝 Update usage with docker in README.md (#33)
- 👷 Add python3.10 to CI

## 0.4.2

- 🐛 Fix config file not used correctly (#27)

## 0.4.1

- 📝 Add more examples regarding #20
- 🐛 Fix devpars by default a Namespace rather than a dict (#21, #22)

## 0.4.0

- ⬆️ Drop support for python 3.8 (brentp/cyvcf2#181)
- 🚨 Use python3.9 in Dockerfile
- ⬆️️ Upgrade pyparam to 0.5
- ⬆️ Upgrade and pin deps
- 📝 Add more examples (#15, #17)
- 👷 Add docker build in CI

## 0.3.0

- Introduce enhancements (pwwang/vcfstats#15)

## 0.2.0
- Use `plotnine` instead of `ggplot2` so no `R` is needed
- Add `figfmt` to generate different format of figures other than `png`

## 0.1.0
- Allow program to be run by `python -m vcfstats`
- Avoid using root logger configuration

## 0.0.6
- Adopt latest pyparam

## 0.0.5
- Adopt lastest cmdy

## 0.0.4
- Add original formula in the error message if it is malformated
- Add warnings if failed to fetch sample depth for a variant
- Fix a bug when continuous filter has zero
- Other fixes

## 0.0.3
- Fix `CAT ~ CAT` plots
- Use pie chart for `CAT ~ 1` as default

## 0.0.2
- Add tests and fix bugs

## 0.0.1
- Implement basic functions
