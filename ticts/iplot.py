"""
isort: skip_file
"""

import logging

logger = logging.getLogger(__name__)

try:
    from bokeh.plotting import figure, show as bokeh_show
    BOKEH_IMPORTED = True
except ImportError:
    BOKEH_IMPORTED = False
    MSG_ERROR = ("'bokeh' is not installed. "
                 "Interactive Plot is not available. "
                 "Install it by using:\npip install bokeh")
    logger.debug(MSG_ERROR)


class TictsPlot:
    def _get_figure(self, title, dot_color, dot_size, **kwargs):
        kwargs = dict(
            title=title or self.name,
            x_axis_type="datetime",
            x_axis_label="timestamp",
            **kwargs)

        p = figure(**kwargs)

        p.step(
            self.index,
            self.values(),
            line_width=2,
            line_dash="4 4",
            mode="after")
        p.circle(
            self.index, self.values(), fill_color=dot_color, size=dot_size)

        return p

    def iplot(self,
              title=None,
              show=False,
              dot_color="red",
              dot_size=6,
              **kwargs):
        if not BOKEH_IMPORTED:
            raise ImportError(MSG_ERROR)

        fig = self._get_figure(
            title=title, dot_color=dot_color, dot_size=dot_size, **kwargs)

        if show:
            bokeh_show(fig)

        return fig
