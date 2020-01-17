"""Handling one plot/instance"""
from os import path
import string
import cmdy
from . import LOGGER
from .formula import Formula, Term, Aggr


def title_to_valid_path(title,
                        allowed='_-.()' + string.ascii_letters +
                        string.digits):
    """Convert a title to a valid file path"""
    return ''.join(c if c in allowed else '_' for c in title)


def get_plot_type(formula, figtype):
    """Get the real plot type"""
    # pylint: disable=too-many-branches,too-many-return-statements
    if isinstance(formula.Y, Aggr) and isinstance(formula.X, Aggr):
        if figtype in ('', None, 'scatter'):
            return figtype or 'scatter'
        raise TypeError("Don't know how to plot AGGREGATION ~ AGGREGATION "
                        "using plots other than scatter")
    if isinstance(formula.Y, Aggr) and isinstance(formula.X, Term):
        if figtype in ('', None, 'col', 'bar', 'pie'):
            figtype = 'col' if figtype == 'bar' else figtype
            return (figtype or 'pie') if formula.X.name == '1' else (figtype
                                                                     or 'col')
        raise TypeError("Don't know how to plot AGGREGATION ~ CATEGORICAL "
                        "using plots other than col/pie")
    # all are terms, 'cuz we cannot have Term ~ Aggr
    # if isinstance(formula.Y, Term) and isinstance(formula.X, Term):
    if formula.Y.term['type'] == 'categorical' and formula.X.term[
            'type'] == 'categorical':
        if figtype in ('', None, 'bar', 'pie'):
            return figtype or 'bar'
        raise TypeError("Don't know how to plot CATEGORICAL ~ CATEGORICAL "
                        "using plots other than bar/pie")
    if formula.Y.term['type'] == 'continuous' and formula.X.term[
            'type'] == 'categorical':
        if figtype in ('', None, 'violin', 'boxplot', 'histogram', 'density',
                       'freqpoly'):
            return figtype or 'violin'
        raise TypeError("Don't know how to plot CONTINUOUS ~ CATEGORICAL " + \
            "using plots other than violin/boxplot/histogram/density/freqpoly")
    if formula.Y.term['type'] == 'categorical' and formula.X.term[
            'type'] == 'continuous':
        if formula.X.term['func'].__name__ == '_ONE':
            if figtype in ('', None, 'bar', 'pie'):
                return figtype or 'pie'
        raise TypeError("If you want to plot CATEGORICAL ~ CONTINUOUS, " + \
            "where CONTINUOUS is not 1, transpose CONTINUOUS ~ CATEGORICAL")
    if formula.Y.term['type'] == 'continuous' and formula.X.term[
            'type'] == 'continuous':
        if formula.X.term['func'].__name__ == '_ONE':
            if figtype in ('', None, 'histogram', 'freqpoly', 'density'):
                return figtype or 'histogram'
            raise TypeError("Don't know how to plot distribution " + \
                "using plots other than histogram/freqpoly/density")
        if figtype in ('', None, 'scatter'):
            return figtype or 'scatter'
        raise TypeError("Don't know how to plot CONTINUOUS ~ CONTINUOUS "
                        "using plots other than scatter")
    return None

class One:
    """One instance/plot"""
    def __init__(self,  # pylint: disable=too-many-arguments
                 formula,
                 title,
                 ggs,
                 devpars,
                 outdir,
                 samples,
                 figtype,
                 passed):

        LOGGER.info("INSTANCE: %r", title)
        self.title = title
        self.formula = Formula(formula, samples, passed, title)
        self.outprefix = path.join(outdir, title_to_valid_path(title))
        self.devpars = devpars
        self.ggs = ggs
        self.datafile = open(self.outprefix + '.txt', 'w')
        if isinstance(self.formula.Y, Aggr) and \
            ((isinstance(self.formula.X, Term) and self.formula.Y.xgroup) or \
            isinstance(self.formula.X, Aggr)):
            self.datafile.write("{}\t{}\tGroup\n".format(
                self.formula.Y.name, self.formula.X.name))
        else:
            self.datafile.write("{}\t{}\n".format(self.formula.Y.name,
                                                  self.formula.X.name))
        self.figtype = get_plot_type(self.formula, figtype)
        LOGGER.info("[%s] plot type: %s", self.title, self.figtype)
        LOGGER.debug("[%s] ggs: %s", self.title, self.ggs)
        LOGGER.debug("[%s] devpars: %s", self.title, self.devpars)

    def __del__(self):
        try:
            if self.datafile:
                self.datafile.close()
        except Exception:
            pass

    def iterate(self, variant):
        """Iterate over each variant"""
        # Y
        self.formula.run(variant, self.datafile)

    def summarize(self):
        """Calculate the aggregations"""
        LOGGER.info("[%s] Summarizing aggregations ...", self.title)
        self.formula.done(self.datafile)
        self.datafile.close()

    def plot(self, Rscript):  # pylint: disable=invalid-name
        """Plot the figures using R"""
        LOGGER.info("[%s] Composing R code ...", self.title)
        rcode = """
            require('ggplot2')
            set.seed(8525)
            figtype = {figtype!r}

            plotdata = read.table(	paste0({outprefix!r}, '.txt'),
                                    header = TRUE, row.names = NULL, check.names = FALSE, sep = "\t")
            cnames = make.unique(colnames(plotdata))
            colnames(plotdata) = cnames

            bQuote = function(s) paste0('`', s, '`')

            png(paste0({outprefix!r}, '.', figtype, '.png'),
                height = {devpars[height]}, width = {devpars[width]}, res = {devpars[res]})
            if (length(cnames) > 2) {{
                aes_for_geom = aes_string(fill = bQuote(cnames[3]))
                aes_for_geom_color = aes_string(color = bQuote(cnames[3]))
                plotdata[,3] = factor(plotdata[,3], levels = rev(unique(as.character(plotdata[,3]))))
            }} else {{
                aes_for_geom = NULL
                aes_for_geom_color = NULL
            }}
            p = ggplot(plotdata, aes_string(y = bQuote(cnames[1]), x = bQuote(cnames[2])))
            xticks = theme(axis.text.x = element_text(angle = 60, hjust = 1))
            if (figtype == 'scatter') {{
                p = p + geom_point(aes_for_geom_color)
            # }} else if (figtype == 'line') {{
            # 	p = p + geom_line(aes_for_geom)
            }} else if (figtype == 'bar') {{
                p = ggplot(plotdata, aes_string(x = bQuote(cnames[2])))
                p = p + geom_bar(aes_string(fill = bQuote(cnames[1]))) + xticks
            }} else if (figtype == 'col') {{
                p = p + geom_col(aes_for_geom) + xticks
            }} else if (figtype == 'pie') {{
                library(ggrepel)
                if (length(cnames) > 2) {{
                    p = p + geom_col(aes_for_geom) + coord_polar("y", start=0) +
                        geom_label_repel(
                            aes_for_geom,
                            y = cumsum(plotdata[,1]) - plotdata[,1]/2,
                            label = paste0(unlist(round(plotdata[,1]/sum(plotdata[,1])*100,1)), '%'),
                            show.legend = FALSE)
                }} else {{
                    plotdata[,1] = factor(plotdata[,1], levels = rev(unique(as.character(plotdata[,1]))))
                    fills = rev(levels(plotdata[,1]))
                    sums  = sapply(fills, function(f) sum(plotdata[,1] == f))
                    p = ggplot(plotdata, aes_string(x = bQuote(cnames[2]))) +
                        geom_bar(aes_string(fill = bQuote(cnames[1]))) + coord_polar("y", start=0) +
                        geom_label_repel(
                            inherit.aes = FALSE,
                            data = data.frame(sums, fills),
                            x = 1,
                            y = cumsum(sums) - sums/2,
                            label = paste0(unlist(round(sums/sum(sums)*100,1)), '%'),
                            show.legend = FALSE)
                }}
                p = p + theme_minimal() + theme(axis.title.x = element_blank(),
                    axis.title.y = element_blank(),
                    axis.text.y =element_blank())
            }} else if (figtype == 'violin') {{
                p = p + geom_violin(aes_for_geom) + xticks
            }} else if (figtype == 'boxplot') {{
                p = p + geom_boxplot(aes_for_geom) + xticks
            }} else if (figtype == 'histogram' || figtype == 'density') {{
                plotdata[,2] = as.factor(plotdata[,2])
                p = ggplot(plotdata, aes_string(x = bQuote(cnames[1])))
                params = list(alpha = .6)
                if (cnames[2] != '1') {{
                    params$mapping = aes_string(fill = bQuote(cnames[2]))
                }}
                p = p + do.call(paste0("geom_", figtype), params)
            }} else if (figtype == 'freqpoly') {{
                plotdata[,2] = as.factor(plotdata[,2])
                p = ggplot(plotdata, aes_string(x = bQuote(cnames[1])))
                if (cnames[2] != '1') {{
                    params$mapping = aes_string(color = bQuote(cnames[2]))
                }}
                p = p + do.call(paste0("geom_", figtype), params)
            }} else {{
                stop(paste('Unknown plot type:', figtype))
            }}
            {extrggs}
            print(p)
            dev.off()
        """.format(figtype=self.figtype,
                   outprefix=self.outprefix,
                   devpars=self.devpars,
                   extrggs=('p = p + ' + self.ggs) if self.ggs else '')
        with open(self.outprefix + '.plot.R', 'w') as fout:
            fout.write(rcode)
        LOGGER.info("[%s] Running R code to plot ...", self.title)
        LOGGER.info("[%s] Data will be saved to: %s", self.title,
                    self.outprefix + '.txt')
        LOGGER.info("[%s] Plot will be saved to: %s", self.title,
                    self.outprefix + '.' + self.figtype + '.png')
        cmd = cmdy.Rscript(self.outprefix + '.plot.R',
                           _exe=Rscript,
                           _raise=False)
        if cmd.rc != 0:
            for line in cmd.stderr.splitlines():
                LOGGER.error("[%s] %s", self.title, line)
