"""Handling one plot/instance"""
from os import path

import pandas
import plotnine as p9
import plotnine_prism as p9p
from datar.base import (
    as_character,
    cumsum,
    factor,
    levels,
    make_unique,
    paste0,
    rev,
    round_,
    sum_,
    unique,
)
from diot import Diot
from slugify import slugify

from .formula import Aggr, Formula, Term
from .utils import logger

GGS_ENV = {
    **{attr: getattr(p9, attr) for attr in dir(p9) if not attr.startswith("_")},
    **{
        attr: getattr(p9p, attr)
        for attr in dir(p9p)
        if not attr.startswith("_")
    },
}


def get_plot_type(formula, figtype):
    """Get the real plot type"""
    # pylint: disable=too-many-branches,too-many-return-statements
    if isinstance(formula.Y, Aggr) and isinstance(formula.X, Aggr):
        if figtype in ("", None, "scatter"):
            return figtype or "scatter"
        raise TypeError(
            "Don't know how to plot AGGREGATION ~ AGGREGATION "
            "using plots other than scatter"
        )
    if isinstance(formula.Y, Aggr) and isinstance(formula.X, Term):
        if figtype in ("", None, "col", "bar", "pie"):
            figtype = "col" if figtype == "bar" else figtype
            return (
                (figtype or "pie")
                if formula.X.name == "1"
                else (figtype or "col")
            )
        raise TypeError(
            "Don't know how to plot AGGREGATION ~ CATEGORICAL "
            "using plots other than col/pie"
        )
    # all are terms, 'cuz we cannot have Term ~ Aggr
    # if isinstance(formula.Y, Term) and isinstance(formula.X, Term):
    if (
        formula.Y.term["type"] == "categorical"
        and formula.X.term["type"] == "categorical"
    ):
        if figtype in ("", None, "bar", "pie"):
            return figtype or "bar"
        raise TypeError(
            "Don't know how to plot CATEGORICAL ~ CATEGORICAL "
            "using plots other than bar/pie"
        )
    if (
        formula.Y.term["type"] == "continuous"
        and formula.X.term["type"] == "categorical"
    ):
        if figtype in (
            "",
            None,
            "violin",
            "boxplot",
            "histogram",
            "density",
            "freqpoly",
        ):
            return figtype or "violin"
        raise TypeError(
            "Don't know how to plot CONTINUOUS ~ CATEGORICAL "
            + "using plots other than violin/boxplot/histogram/density/freqpoly"
        )
    if (
        formula.Y.term["type"] == "categorical"
        and formula.X.term["type"] == "continuous"
    ):
        if formula.X.term["func"].__name__ == "_ONE":
            if figtype in ("", None, "bar", "pie"):
                return figtype or "pie"
        raise TypeError(
            "If you want to plot CATEGORICAL ~ CONTINUOUS, "
            + "where CONTINUOUS is not 1, transpose CONTINUOUS ~ CATEGORICAL"
        )
    if (
        formula.Y.term["type"] == "continuous"
        and formula.X.term["type"] == "continuous"
    ):
        if formula.X.term["func"].__name__ == "_ONE":
            if figtype in ("", None, "histogram", "freqpoly", "density"):
                return figtype or "histogram"
            raise TypeError(
                "Don't know how to plot distribution "
                + "using plots other than histogram/freqpoly/density"
            )
        if figtype in ("", None, "scatter"):
            return figtype or "scatter"
        raise TypeError(
            "Don't know how to plot CONTINUOUS ~ CONTINUOUS "
            "using plots other than scatter"
        )
    return None


class Instance:
    """One instance/plot"""

    def __init__(
        self,  # pylint: disable=too-many-arguments
        formula,
        title,
        ggs,
        devpars,
        outdir,
        samples,
        figtype,
        passed,
    ):

        logger.info("INSTANCE: %r", title)
        self.title = title
        self.formula = Formula(formula, samples, passed, title)
        self.outprefix = path.join(outdir, slugify(title))
        self.devpars = devpars
        self.ggs = ggs
        self.data = []
        self.datacols = [self.formula.Y.name, self.formula.X.name]
        if isinstance(self.formula.Y, Aggr) and (
            (isinstance(self.formula.X, Term) and self.formula.Y.xgroup)
            or isinstance(self.formula.X, Aggr)
        ):
            self.datacols.append("Group")
        self.figtype = get_plot_type(self.formula, figtype)
        logger.info("[%s] plot type: %s", self.title, self.figtype)
        logger.debug("[%s] ggs: %s", self.title, self.ggs)
        logger.debug("[%s] devpars: %s", self.title, self.devpars)

    def __del__(self):
        del self.data

    def iterate(self, variant):
        """Iterate over each variant"""
        # Y
        self.formula.run(variant, self.data.append, self.data.extend)

    def summarize(self):
        """Calculate the aggregations"""
        logger.info("[%s] Summarizing aggregations ...", self.title)
        self.formula.done(self.data.append, self.data.extend)

    def plot(self, Rscript):  # pylint: disable=invalid-name
        """Plot the figures using R"""
        df = pandas.DataFrame(  # pylint: disable=invalid-name
            self.data,
            columns=self.datacols,
        )
        df.columns = make_unique(df.columns.tolist())
        aes_for_geom_fill = None
        aes_for_geom_color = None
        if df.shape[1] > 2:
            aes_for_geom_fill = p9.aes(fill=df.columns[2])
            aes_for_geom_color = p9.aes(color=df.columns[2])
        plt = p9.ggplot(df, p9.aes(y=df.columns[0], x=df.columns[1]))
        if self.figtype == "scatter":
            plt = plt + p9.geom_point(aes_for_geom_color)
        elif self.figtype == "line":
            pass
        elif self.figtype == "bar":
            plt = plt + p9.geom_bar(p9.aes(fill=df.columns[0])) + p9.theme(
                axis_text_x=p9.element_text(angle=60, hjust=1)
            )
        elif self.figtype == "col":
            plt = plt + p9.geom_col(aes_for_geom_fill) + p9.theme(
                axis_text_x=p9.element_text(angle=60, hjust=1)
            )
        elif self.figtype == "pie":
            col0 = df.iloc[:, 0]
            if df.shape[1] > 2:
                plt = plt + p9.geom_label(
                    aes_for_geom_fill,
                    y=cumsum(col0) - col0 / 2.0,
                    label=paste0(round_(100 * col0 / sum_(col0), 1), "%"),
                    show_legend=False,
                    position=p9.position_adjust_text(),
                )
            else:
                col0 = factor(col0, levels=rev(unique(as_character(col0))))
                fills = rev(levels(col0))
                sums = map(lambda x: sum(col0 == x), fills)
                plt = (
                    p9.ggplot(df, p9.aes(x=df.columns[1]))
                    + p9.geom_bar(p9.aes(fill=df.columns[0]))
                    + p9.geom_label(
                        x=1,
                        y=cumsum(sums) - sums / 2,
                        label=paste0(round(sums / sum(sums) * 100, 1), "%"),
                        show_legend=False,
                    )
                    + p9.theme(
                        axis_title_x=p9.element_blank(),
                        axis_title_y=p9.element_blank(),
                        axis_text_y=p9.element_blank(),
                    )
                )
        elif self.figtype == "violin":
            plt = p9.geom_violin(aes_for_geom_fill) + p9.theme(
                axis_text_x=p9.element_text(angle=60, hjust=1)
            )
        elif self.figtype == "boxplot":
            plt = p9.geom_boxplot(aes_for_geom_fill) + p9.theme(
                axis_text_x=p9.element_text(angle=60, hjust=1)
            )
        elif self.figtype in ("histogram", "density"):
            col1 = factor(df.iloc[:, 1])
            plt = p9.ggplot(df, p9.aes(x=df.columns[0]))
            geom = getattr(p9, f"geom_{self.figtype}")
            if df.columns[1] != "1":
                plt = plt + geom(p9.aes(color=df.columns[1]), alpha=0.6)
            else:
                plt = plt + geom(alpha=0.6)
        elif self.figtype == "freqpoly":
            col1 = factor(df.iloc[:, 1])
            plt = p9.ggplot(df, p9.aes(x=df.columns[0]))
            if df.columns[1] != "1":
                plt = plt + p9.geom_freqpoly(p9.aes(color=df.columns[1]))
            else:
                plt = plt + p9.geom_freqpoly()
        else:
            raise ValueError(f"Unknown figure type: {self.figtype}")

        plt = plt + p9.ggtitle(self.title)
        self.save_plot(plt)

    def save_plot(self, plt):
        ggs = []
        has_theme = False
        for i, gg in enumerate(ggs):
            ggcode = compile(
                f"__gg__ = {gg}", f"<vcfstats-ggs-{i}>", mode="exec"
            )
            try:
                # pylint: disable=exec-used
                exec(ggcode, GGS_ENV)
            except Exception as exc:
                raise ValueError(f"Invalid ggs expression: {gg}") from exc
            ggs.append(GGS_ENV.pop("__gg__"))
            if gg.startswith("theme_"):
                has_theme = True
        if not has_theme:
            plt += p9p.theme_prism(base_size=12)

        devpars = (
            Diot(height=1000, width=1000, res=100, format="png") | self.devpars
        )
        devpars.height /= devpars.res
        devpars.width /= devpars.res
        figfile = f"{self.outprefix}.{self.figtype}.{devpars.format}"
        plt.save(
            filename=figfile,
            verbose=False,
            width=devpars.width,
            height=devpars.height,
            dpi=devpars.res,
        )
        logger.info("[%s] plot saved to: %s", self.title, figfile)
