from typing import Any

import plotly.graph_objects as go

from optimagic.config import (
    IS_ALTAIR_INSTALLED,
    IS_BOKEH_INSTALLED,
    IS_MATPLOTLIB_INSTALLED,
    IS_SEABORN_INSTALLED,
)
from optimagic.exceptions import InvalidPlottingBackendError, NotInstalledError
from optimagic.visualization.plotting_utilities import LineData


def _is_jupyter():
    try:
        from IPython import get_ipython

        return (
            get_ipython() is not None
            and get_ipython().__class__.__name__ == "ZMQInteractiveShell"
        )
    except ImportError:
        return False


if IS_MATPLOTLIB_INSTALLED:
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    # Handle the case where matplotlib is used in notebooks (inline backend)
    # to ensure that interactive mode is disabled to avoid double plotting.
    # (See: https://github.com/matplotlib/matplotlib/issues/26221)
    if mpl.get_backend() == "module://matplotlib_inline.backend_inline":
        plt.install_repl_displayhook()
        plt.ioff()

if IS_SEABORN_INSTALLED:
    import seaborn as sns

if IS_BOKEH_INSTALLED:
    from bokeh.io import curdoc, output_notebook
    from bokeh.plotting import figure as bokeh_figure

    if _is_jupyter():
        output_notebook()

if IS_ALTAIR_INSTALLED:
    import altair as alt
    import pandas as pd


def _line_plot_plotly(
    lines: list[LineData],
    *,
    template: str | None,
    legend_properties: dict[str, Any] | None,
    xlabel: str | None,
    ylabel: str | None,
) -> Any:
    fig = go.Figure()

    if template is not None:
        fig.update_layout(template=template)

    for line in lines:
        fig.add_trace(
            go.Scatter(
                x=line.x,
                y=line.y,
                mode="lines",
                name=line.name,
                line=dict(color=line.color),
            )
        )

    fig.update_layout(
        legend=legend_properties,
        xaxis_title=xlabel,
        yaxis_title=ylabel,
    )

    return fig


def _line_plot_matplotlib(
    lines: list[LineData],
    *,
    template: str | None,
    legend_properties: dict[str, Any] | None,
    xlabel: str | None,
    ylabel: str | None,
) -> Any:
    if not IS_MATPLOTLIB_INSTALLED:
        raise NotInstalledError("Matplotlib is not installed...")

    if template is not None:
        plt.style.use(template)

    fig, ax = plt.subplots()

    for line in lines:
        ax.plot(
            line.x,
            line.y,
            label=line.name if line.show_in_legend else None,
            color=line.color,
        )

    ax.set(xlabel=xlabel, ylabel=ylabel)
    ax.legend(**legend_properties)

    return fig


def _line_plot_seaborn(
    lines: list[LineData],
    *,
    template: str | None,
    legend_properties: dict[str, Any] | None,
    xlabel: str | None,
    ylabel: str | None,
) -> Any:
    if not IS_SEABORN_INSTALLED:
        raise NotInstalledError("Seaborn is not installed...")

    if template is not None:
        sns.set_theme(style=template)

    fig, ax = plt.subplots()

    for line in lines:
        sns.lineplot(
            x=line.x,
            y=line.y,
            label=line.name if line.show_in_legend else None,
            color=line.color,
            ax=ax,
        )

    ax.set(xlabel=xlabel, ylabel=ylabel)
    ax.legend(**legend_properties)

    return fig


def _line_plot_bokeh(
    lines: list[LineData],
    *,
    template: str | None,
    legend_properties: dict[str, Any] | None,
    xlabel: str | None,
    ylabel: str | None,
) -> Any:
    if not IS_BOKEH_INSTALLED:
        raise NotInstalledError("Bokeh is not installed...")

    if template is not None:
        curdoc().theme = template

    fig = bokeh_figure(title="Line Plot", x_axis_label=xlabel, y_axis_label=ylabel)

    for line in lines:
        fig.line(
            line.x,
            line.y,
            legend_label=line.name if line.show_in_legend else None,
            line_color=line.color,
        )

    if legend_properties:
        for prop, value in legend_properties.items():
            if hasattr(fig.legend, prop):
                setattr(fig.legend, prop, value)

    return fig


def _line_plot_altair(
    lines: list[LineData],
    *,
    template: str | None,
    legend_properties: dict[str, Any] | None,
    xlabel: str | None,
    ylabel: str | None,
) -> Any:
    if not IS_ALTAIR_INSTALLED:
        raise NotInstalledError("Altair is not installed...")

    if template is not None:
        alt.themes.enable(template)

    data = pd.DataFrame(
        {
            "x": [point for line in lines for point in line.x],
            "y": [point for line in lines for point in line.y],
            "name": [line.name for line in lines for _ in line.x],
            "color": [line.color for line in lines for _ in line.x],
        }
    )

    chart = (
        alt.Chart(data)
        .mark_line()
        .encode(
            x=alt.X("x", title=xlabel),
            y=alt.Y("y", title=ylabel),
            color=alt.Color("color"),
            tooltip=["name"],
        )
    )

    return chart


BACKEND_TO_LINE_PLOT_FUNC = {
    "plotly": _line_plot_plotly,
    "matplotlib": _line_plot_matplotlib,
    "seaborn": _line_plot_seaborn,
    "bokeh": _line_plot_bokeh,
    "altair": _line_plot_altair,
}


def line_plot(
    lines: list[LineData],
    *,
    backend: str,
    template: str | None,
    legend_properties: dict[str, Any] | None,
    xlabel: str | None,
    ylabel: str | None,
) -> Any:
    # check for valid backend
    if backend not in BACKEND_TO_LINE_PLOT_FUNC:
        raise InvalidPlottingBackendError(
            f"Invalid plotting backend '{backend}'. "
            f"Available backends: {', '.join(BACKEND_TO_LINE_PLOT_FUNC.keys())}."
        )

    _line_plot_backend_function = BACKEND_TO_LINE_PLOT_FUNC[backend]
    fig = _line_plot_backend_function(
        lines=lines,
        template=template,
        legend_properties=legend_properties,
        xlabel=xlabel,
        ylabel=ylabel,
    )

    return fig
