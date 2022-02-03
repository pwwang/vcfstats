"""Handling one plot/instance"""
from os import path
from types import ModuleType

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
    unique,
)
from diot import Diot
from slugify import slugify

from .formula import Aggr, Formula, Term
from .utils import capture_c_msg, capture_python_msg, logger

GGS_ENV = {
    **{
        attr: getattr(p9, attr) for attr in dir(p9) if not attr.startswith("_")
    },
    **{
        attr: getattr(p9p, attr)
        for attr in dir(p9p)
        if not attr.startswith("_")
        and not isinstance(getattr(p9p, attr), ModuleType)
    },
}


def get_plot_type(formula, figtype):
    """Get the real plot type"""
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
                if formula.X.name == "ONE"
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
            "using plots other than violin/boxplot/histogram/density/freqpoly"
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
            "where CONTINUOUS is not 1, transpose CONTINUOUS ~ CATEGORICAL"
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
                "using plots other than histogram/freqpoly/density"
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
        self,
        formula,
        title,
        ggs,
        devpars,
        outdir,
        samples,
        figtype,
        passed,
        savedata=False,
        figfmt="png",
    ):

        logger.info(
            "[r]INSTANCE[/r]: %r",
            title,
            extra={"markup": True},
        )
        self.title = title
        self.formula = Formula(formula, samples, passed, title)
        self.outprefix = path.join(outdir, slugify(title))
        self.devpars = devpars
        self.ggs = ggs or ""
        self.data = []
        self.savedata = savedata
        self.datacols = [self.formula.Y.name, self.formula.X.name]
        if isinstance(self.formula.Y, Aggr) and (
            (isinstance(self.formula.X, Term) and self.formula.Y.xgroup)
            or isinstance(self.formula.X, Aggr)
        ):
            self.datacols.append("Group")
        self.figtype = get_plot_type(self.formula, figtype)
        self.figfmt = figfmt
        logger.info(
            "[r]%s[/r]: plot type: %s",
            self.title,
            self.figtype,
            extra={"markup": True},
        )
        logger.debug(
            "[r]%s[/r]: ggs: %s",
            self.title,
            self.ggs,
            extra={"markup": True},
        )
        logger.debug(
            "[r]%s[/r]: devpars: %s",
            self.title,
            self.devpars,
            extra={"markup": True},
        )

    def __del__(self):
        del self.data

    def iterate(self, variant):
        """Iterate over each variant"""
        # Y
        self.formula.run(variant, self.data.append, self.data.extend)

    def summarize(self):
        """Calculate the aggregations"""
        logger.info(
            "[r]%s[/r]: Summarizing aggregations ...",
            self.title,
            extra={"markup": True},
        )
        self.formula.done(self.data.append, self.data.extend)

    def plot(self):
        """Plot the figures using R"""
        df = pandas.DataFrame(
            self.data,
            columns=self.datacols,
        )
        with capture_c_msg("datar", prefix=f"[r]{self.title}[/r]: "):
            df.columns = make_unique(df.columns.tolist())

        if self.savedata:
            datafile = self.outprefix + ".csv"
            logger.info(
                "[r]%s[/r]: Saving data to: %r",
                self.title,
                datafile,
                extra={"markup": True},
            )
            df.to_csv(datafile, index=False)

        if df.shape[0] == 0:
            logger.warning("No data points to plot")
            return

        aes_for_geom_fill = None
        aes_for_geom_color = None
        theme_elems = p9.theme(axis_text_x=p9.element_text(angle=60, hjust=2))
        if df.shape[1] > 2:
            aes_for_geom_fill = p9.aes(fill=df.columns[2])
            aes_for_geom_color = p9.aes(color=df.columns[2])
        plt = p9.ggplot(df, p9.aes(y=df.columns[0], x=df.columns[1]))
        if self.figtype == "scatter":
            plt = plt + p9.geom_point(aes_for_geom_color)
            theme_elems = None
        elif self.figtype == "line":
            pass
        elif self.figtype == "bar":
            plt = plt + p9.geom_bar(p9.aes(fill=df.columns[0]))
        elif self.figtype == "col":
            plt = plt + p9.geom_col(aes_for_geom_fill)
        elif self.figtype == "pie":
            logger.warning(
                "Pie chart is not support by plotnine yet, "
                "plotting bar chart instead."
            )
            col0 = df.iloc[:, 0]
            if df.shape[1] > 2:
                plt = plt + p9.geom_bar(
                    p9.aes(x=df.columns[2], y=col0.name, fill=df.columns[2]),
                    stat="identity",
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
                )
                theme_elems = p9.theme(
                    axis_title_x=p9.element_blank(),
                    axis_title_y=p9.element_blank(),
                    axis_text_y=p9.element_blank(),
                )
        elif self.figtype == "violin":
            plt = plt + p9.geom_violin(aes_for_geom_fill)
        elif self.figtype == "boxplot":
            plt = plt + p9.geom_boxplot(aes_for_geom_fill)
        elif self.figtype in ("histogram", "density"):
            plt = p9.ggplot(df, p9.aes(x=df.columns[0]))
            geom = getattr(p9, f"geom_{self.figtype}")
            if df.columns[1] != "ONE":
                plt = plt + geom(p9.aes(fill=df.columns[1]), alpha=0.6)
                theme_elems = None
            else:
                plt = plt + geom(alpha=0.6)
                theme_elems = p9.theme(legend_position="none")
        elif self.figtype == "freqpoly":
            plt = p9.ggplot(df, p9.aes(x=df.columns[0]))
            if df.columns[1] != "ONE":
                plt = plt + p9.geom_freqpoly(p9.aes(fill=df.columns[1]))
            else:
                plt = plt + p9.geom_freqpoly()
            theme_elems = None
        else:
            raise ValueError(f"Unknown figure type: {self.figtype}")

        plt = plt + p9.ggtitle(self.title)
        self.save_plot(plt, theme_elems)

    def save_plot(self, plt, theme_elems):
        has_theme = False
        theme_frags = []
        for i, gg in enumerate(self.ggs.split(";")):
            gg = gg.strip()
            if not gg:
                continue
            ggcode = compile(
                f"__gg__ = {gg}", f"<vcfstats-ggs-{i}>", mode="exec"
            )
            try:
                exec(ggcode, GGS_ENV)
            except Exception as exc:
                raise ValueError(f"Invalid ggs expression: {gg}") from exc

            ggexpr = GGS_ENV.pop("__gg__")
            # avoid user theme fragments being overriden by theme_prism
            if gg.startswith("theme("):
                theme_frags.append(ggexpr)
            else:
                plt = plt + ggexpr
                if gg.startswith("theme_"):
                    has_theme = True

        if not has_theme:
            plt = plt + p9p.theme_prism(base_size=12, base_family="monospace")
        plt = plt + theme_elems
        for theme_frag in theme_frags:
            plt = plt + theme_frag

        devpars = (
            Diot(height=1000, width=1000, res=100, format=self.figfmt)
            | self.devpars
        )
        devpars.height /= devpars.res
        devpars.width /= devpars.res
        figfile = f"{self.outprefix}.{self.figtype}.{devpars.format}"
        with capture_python_msg("plotnine", prefix=f"[r]{self.title}[/r]: "):
            plt.save(
                filename=figfile,
                verbose=False,
                width=devpars.width,
                height=devpars.height,
                dpi=devpars.res,
            )
        logger.info(
            "[r]%s[/r]: plot saved to: %s",
            self.title,
            figfile,
            extra={"markup": True},
        )
