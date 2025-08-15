import pandas as pd

from optimagic.benchmarking.process_benchmark_results import (
    process_benchmark_results,
)
from optimagic.config import DEFAULT_PALETTE
from optimagic.visualization.backends import line_plot
from optimagic.visualization.plotting_utilities import LineData, get_palette_cycle


def deviation_plot(
    problems,
    results,
    *,
    backend="plotly",
    runtime_measure="n_evaluations",
    distance_measure="criterion",
    monotone=True,
    template=None,
):
    """Plot average convergence of optimizers for a set of problems.

    Returns aggregated version convergence plot, showing the convergence of the
    different algorithms, averaged over a problem set. The faster a line falls, the
    faster the algorithm improved on average.

    The x axis is the runtime_measure, which can be walltime or number of evaluations.
    The y axis is the average over the convergence measures of the problems in the set.
    Convergence can be measured by the criterion value of the particular
    time/evaluation. The convergence can be made monotone by always taking the
    best  value.

    Args:
        problems (dict): optimagic benchmarking problems dictionary. Keys are the
            problem names. Values contain information on the problem, including the
            solution value.
        results (dict): optimagic benchmarking results dictionary. Keys are
            tuples of the form (problem, algorithm), values are dictionaries of the
            collected information on the benchmark run, including 'criterion_history'
            and 'time_history'.
        runtime_measure (str): One of "n_evaluations", "n_batches".
        distance_measure (str): One of "criterion", "parameter_distance".
        monotone (bool): If True the best found criterion value so far is plotted.
            If False the particular criterion evaluation of that time is used.
        template (str): The template for the figure. Default is "plotly_white".

    Returns:
        plotly.Figure

    """
    df, _ = process_benchmark_results(
        problems=problems,
        results=results,
        stopping_criterion="y",
        x_precision=1e-6,
        y_precision=1e-6,
    )

    outcome = f"{'monotone_' if monotone else ''}" + distance_measure + "_normalized"
    deviations = (
        df.groupby(["problem", "algorithm", runtime_measure])
        .min()[outcome]
        .reindex(
            pd.MultiIndex.from_product(
                [
                    df["problem"].unique(),
                    df["algorithm"].unique(),
                    range(df[runtime_measure].min(), df[runtime_measure].max() + 1),
                ],
                names=["problem", "algorithm", runtime_measure],
            )
        )
        .ffill()
        .reset_index()
    )
    average_deviations = (
        deviations.groupby(["algorithm", runtime_measure])
        .mean(numeric_only=True)[outcome]
        .reset_index()
    )

    palette_cycle = get_palette_cycle(DEFAULT_PALETTE)
    lines = []

    for algorithm, data in average_deviations.groupby("algorithm"):
        line_data = LineData(
            x=data[runtime_measure],
            y=data[outcome],
            name=algorithm,
            color=next(palette_cycle),
        )
        lines.append(line_data)

    y_labels = {
        "criterion_normalized": "Share of Function Distance to Optimum<br>"
        "Missing From Current Criterion Value",
        "monotone_criterion_normalized": "Share of Function Distance to Optimum<br>"
        "Missing From Best So Far",
        "parameter_distance_normalized": "Share of Parameter Distance to Optimum<br>"
        "Missing From Current Parameters",
        "monotone_parameter_distance_normalized": "Share of the Parameter Distance "
        "to Optimum<br> Missing From the Best Parameters So Far",
    }
    x_labels = {
        "n_evaluations": "Numver of Function Evaluations",
        "n_batches": "Number of Batches",
    }

    fig = line_plot(
        lines=lines,
        backend=backend,
        template=template,
        legend_properties={"title": "Algorithm"},
        xlabel=x_labels[runtime_measure],
        ylabel=y_labels[outcome],
    )

    return fig
