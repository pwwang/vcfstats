"""Handling the formulas"""
from collections import OrderedDict

import numpy
from lark import Lark, Token, Transformer, v_args

from .utils import MACROS, logger, parse_subsets


@v_args(inline=True)
class VcfStatsTransformer(Transformer):
    """Transformer for vcfstats formulas"""

    def start(self, expr1, expr2=None):
        """The start rule"""
        return expr1, expr2 or One()

    def term(self, name, items=None, samples=None):
        """The term rule"""
        return Term(str(name), items, samples)

    def aggr(self, name, term, *kwargs):
        """The aggr rule"""
        aggr_args = []
        aggr_kwargs = {}
        if kwargs:
            if isinstance(kwargs[0], Token):
                for i in range(0, len(kwargs), 2):
                    aggr_kwargs[str(kwargs[i])] = kwargs[i + 1]
            else:
                aggr_args.extend(kwargs)

        return Aggr(str(name), term, *aggr_args, **aggr_kwargs)

    def items(self, *itms):
        """The items rule"""
        return parse_subsets(itms)

    samples = items
    one = lambda _: One()


GRAMMAR = r"""
start: expr ["~" expr | "~"]
?expr: aggr | term
term: NAME [items] [samples]
    | "1" -> one
aggr: NAME "(" term ("," NAME "=" term | "," term)* ")"
items: "[" [ITEM] ("," [ITEM])* "]"
samples: "{" ITEM ("," ITEM)* "}"

NAME: /[A-Za-z_]\w+/
ITEM: /[^\]},]+/
%ignore /\s+/
"""

PARSER = Lark(
    GRAMMAR,
    parser="lalr",
    debug=True,
    maybe_placeholders=True,
    transformer=VcfStatsTransformer(),
)


class Term:
    """The term in the formula"""

    def __init__(self, name, items=None, samples=None):
        self.name = name
        if name not in MACROS:
            raise ValueError("Term {!r} has not been registered.".format(name))
        self.term = MACROS[name]
        self.subsets = items
        self.samples = samples

        if not self.term.get("type"):
            raise TypeError("No type specified for Term: {}".format(self.term))

        if self.term["type"] == "continuous" and self.subsets:
            if len(self.subsets) != 2:
                raise KeyError(
                    "Expect a subset of length 2 for continuous Term: "
                    f"{self.term}"
                )
            if self.subsets[0]:
                self.subsets[0] = float(self.subsets[0])  # try to raise
            if self.subsets[1]:
                self.subsets[1] = float(self.subsets[1])

    def set_samples(self, samples):
        """Set the samples for the term"""
        if self.samples:
            for i, sample in enumerate(self.samples):
                if sample.isdigit():
                    self.samples[i] = int(sample)
                elif sample not in samples:
                    raise ValueError(
                        "Sample {!r} does not exist.".format(sample)
                    )
                else:
                    self.samples[i] = samples.index(sample)

    def __repr__(self):
        if self.subsets and self.samples:
            return "<Term {}(subsets={}, samples={})>".format(
                self.name, self.subsets, self.samples
            )
        if self.subsets:
            return "<Term {}(subsets={})>".format(self.name, self.subsets)
        if self.samples:
            return "<Term {}(samples={})>".format(self.name, self.samples)
        return "<Term {}()>".format(self.name)

    def __eq__(self, other):
        if not isinstance(other, Term):
            return False
        return (
            self.term == other.term
            and self.subsets == other.subsets
            and self.samples == other.samples
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def run(self, variant, passed):
        """Run the variant"""
        if passed and variant.FILTER:
            return False
        value = self.term["func"](variant)

        if value is False or value is None:
            return False
        # numpy.array
        if not hasattr(value, "T") and not isinstance(value, (tuple, list)):
            value = [value]
        if self.samples:
            value = [value[sidx] for sidx in self.samples]

        if self.term["type"] == "continuous" and self.subsets:
            if self.subsets[0] is not None and any(
                val < self.subsets[0] for val in value
            ):
                return False
            if self.subsets[1] is not None and any(
                val > self.subsets[1] for val in value
            ):
                return False
        if self.term["type"] == "categorical" and self.subsets:
            if any(val not in self.subsets for val in value):
                return False
        return value


class One(Term):
    """Term 1"""

    def __init__(self, name="_ONE", items=None, samples=None):
        super().__init__(name, items, samples)


class Aggr:
    """The aggregation"""

    def __init__(self, name, term, *args, **kwargs):
        self.cache = OrderedDict()  # cache data for aggregation
        if name not in MACROS or not MACROS[name].get("aggr"):
            raise ValueError(
                "Aggregation {!r} has not been registered.".format(name)
            )
        self.aggr = MACROS[name]
        if not term:
            raise ValueError("Aggregation has to work with a term.")

        self.term = term
        self.filter = kwargs.get("filter")
        self.group = kwargs.get("group", args[0] if args else None)

        self.name = "{}({})".format(name, self.term.name)
        if self.term.term["type"] != "continuous":
            raise TypeError("Cannot aggregate on categorical data.")

        if self.group and self.group.term["type"] != "categorical":
            raise TypeError("Cannot aggregate on continuous groups.")

        self.xgroup = None

    def __repr__(self):
        return "<Aggr {}({}, filter={}, group={})>".format(
            self.aggr["func"].__name__, self.term, self.filter, self.group
        )

    def has_filter(self):
        """Tell if I have filter"""
        return (
            self.term.name == "FILTER"
            or (self.filter and self.filter.name == "FILTER")
            or (self.group and self.group.name == "FILTER")
        )

    def setxgroup(self, xvar):
        """Set the group of X"""
        if not self.group:
            self.group = xvar
        else:
            self.xgroup = xvar

    def run(self, variant, passed):
        """Run each variant"""
        if self.filter and self.filter.run(variant, passed) is False:
            return

        if not self.group:
            raise RuntimeError(
                "No group specified, don't know how to aggregate."
            )

        group = self.group.run(variant, passed)
        if group is False:
            return

        value = self.term.run(variant, passed)
        if value is False:
            return

        if len(group) > 1 and len(value) != len(group):
            raise ValueError(
                "Cannot aggregate on more than one group, "
                + "make sure you specified sample for sample data."
            )
        # group = group[0]

        xgroup = None
        if self.xgroup:
            xgroup = self.xgroup.run(variant, passed)
            if xgroup is False:
                return
            if len(xgroup) > 1 and len(value) != len(xgroup):
                raise ValueError(
                    "Cannot aggregate on more than one level of xgroup."
                )
            # xgroup = xgroup[0]

        if xgroup is not None:
            for xgrup, grup, val in zip(xgroup, group, value):
                self.cache.setdefault(
                    xgrup, {}
                ).setdefault(
                    grup, []
                ).append(val)
        else:
            for grup, val in zip(group, value):
                self.cache.setdefault(grup, []).append(val)

    def dump(self):
        """Dump and calculate the aggregations"""
        ret = OrderedDict()
        for key, value in self.cache.items():
            if isinstance(value, dict):
                ret[key] = [
                    (self.aggr["func"](val), grup)
                    for grup, val in value.items()
                ]
            else:
                ret[key] = self.aggr["func"](value)
        self.cache.clear()
        return ret


class Formula:
    """Handling the formulas"""

    def __init__(self, formula, samples, passed, title):
        logger.info(
            "[r]%s[/r]: Parsing formulas ...",
            title,
            extra={"markup": True},
        )
        self.Y, self.X = PARSER.parse(formula)
        if isinstance(self.Y, Term):
            self.Y.set_samples(samples)
        if isinstance(self.X, Term):
            self.X.set_samples(samples)
        if isinstance(self.Y, Aggr) and isinstance(self.Y.group, Term):
            self.Y.group.set_samples(samples)
        if isinstance(self.X, Aggr) and isinstance(self.X.group, Term):
            self.X.group.set_samples(samples)
        if isinstance(self.Y, Aggr) and isinstance(self.Y.term, Term):
            self.Y.term.set_samples(samples)
        if isinstance(self.X, Aggr) and isinstance(self.X.term, Term):
            self.X.term.set_samples(samples)

        if isinstance(self.Y, Aggr) and isinstance(self.X, Term):
            self.Y.setxgroup(self.X)
        elif isinstance(self.Y, Aggr) and isinstance(self.X, Aggr):
            if not self.Y.group:
                self.Y.group = self.X.group
            if not self.X.group:
                self.X.group = self.Y.group
            if self.Y.group != self.X.group:
                raise ValueError(
                    "Two aggregations have to group by the same entry."
                )

        self.passed = passed
        if (
            (isinstance(self.Y, Term) and self.Y.name == "FILTER")
            or (isinstance(self.Y, Aggr) and self.Y.has_filter())
            or (isinstance(self.X, Term) and self.X.name == "FILTER")
            or (isinstance(self.X, Aggr) and self.X.has_filter())
        ):
            self.passed = False

    def run(self, variant, data_append, data_extend):
        """Run each variant"""
        if isinstance(self.Y, Term) and isinstance(self.X, Term):
            yvar, xvar = (
                self.Y.run(variant, self.passed),
                self.X.run(variant, self.passed),
            )
            if yvar is False or xvar is False:
                return
            lenx = len(xvar)
            leny = len(yvar)
            if leny != lenx and leny != 1 and lenx != 1:
                raise RuntimeError(
                    "Unmatched length of MACRO results: Y({}), X({})".format(
                        leny, lenx
                    )
                )
            if lenx == 1:
                xvar = xvar * leny
            if leny == 1:
                yvar = yvar * lenx

            data_extend(((yvar[i], rvar) for i, rvar in enumerate(xvar)))
        elif isinstance(self.Y, Aggr) and isinstance(self.X, Aggr):
            self.Y.run(variant, self.passed)
            self.X.run(variant, self.passed)
        elif isinstance(self.Y, Aggr) and isinstance(self.X, Term):
            self.Y.run(variant, self.passed)
        else:
            raise TypeError(
                "Cannot do 'TERM ~ AGGREGATION'. "
                "If you want to do that, transpose it to "
                "'AGGREGATION ~ TERM'"
            )

    def done(self, data_append, data_extend):
        """Done iteration, start summarizing"""
        if isinstance(self.Y, Aggr):
            if isinstance(self.X, Term):
                for key, value in self.Y.dump().items():
                    if isinstance(value, list):
                        data_extend(((val, key, grup) for val, grup in value))
                    else:
                        data_append((value, key))
            else:
                xdump = self.X.dump()
                data_extend(
                    (value, xdump.get(key, numpy.nan), key)
                    for key, value in self.Y.dump().items()
                )
