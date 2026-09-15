import pandas as pd

from treedex.components.plots import make_scatter_plot


def test_make_scatter_plot_forwards_options_and_keeps_species_custom_data():
    frame = pd.DataFrame({
        "Species": ["a", "b", "c"],
        "X": [1.0, 2.0, 3.0],
        "Y": [2.0, 4.0, 3.0],
        "Group": ["one", "two", "one"],
        "Error": [0.1, 0.2, 0.1],
    })

    figure = make_scatter_plot(
        frame,
        x="X",
        y="Y",
        color="Group",
        symbol="Group",
        error_y="Error",
        opacity=0.6,
        range_x_min=0,
        range_x_max=4,
        title="Configured scatter",
        subtitle="Test subtitle",
        selection=[1],
    )

    assert figure.layout.title.text == "Configured scatter"
    assert list(figure.layout.xaxis.range) == [0, 4]
    assert all(trace.customdata is not None for trace in figure.data)
    custom_species = {
        row[0] for trace in figure.data for row in trace.customdata
    }
    assert custom_species == {"a", "b", "c"}
    assert any(trace.selectedpoints for trace in figure.data)


def test_histogram_marginal_does_not_receive_scatter_marker_properties():
    frame = pd.DataFrame({"Species": ["a", "b"], "X": [1.0, 2.0], "Y": [2.0, 3.0]})
    figure = make_scatter_plot(frame, x="X", y="Y", marginal_x="histogram")
    assert {trace.type for trace in figure.data} == {"scatter", "histogram"}
