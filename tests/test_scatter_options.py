import pandas as pd

from treedex.scatter_options import normalize_scatter_options, validate_scatter_options


def sample_frame():
    return pd.DataFrame({
        "Species": ["a", "b", "c"],
        "X": [1.0, 2.0, 3.0],
        "Y": [2.0, 4.0, 8.0],
        "Group": ["one", "two", "one"],
        "Positive": [0.0, 1.0, 2.0],
        "Negative": [-1.0, 0.0, 1.0],
    })


def test_normalization_preserves_compatible_values_and_resets_columns():
    options = normalize_scatter_options(
        {"x": "missing", "color": "Group", "size": "Negative", "hover_data": ["Group", "missing"]},
        sample_frame(),
    )

    assert options["x"] == "X"
    assert options["y"] == "Y"
    assert options["color"] == "Group"
    assert options["size"] is None
    assert options["hover_data"] == ["Group"]


def test_validation_reports_bounds_and_incompatible_combinations():
    options = normalize_scatter_options({}, sample_frame())
    options.update({
        "opacity": 1.2,
        "range_x_min": 10,
        "range_x_max": 1,
        "facet_row": "Group",
        "facet_col_wrap": 2,
        "animation_group": "Species",
        "error_x_minus": "Positive",
    })

    errors = validate_scatter_options(options, sample_frame())

    assert any("Opacity" in error for error in errors)
    assert any("X-axis range" in error for error in errors)
    assert any("Facet column wrap" in error for error in errors)
    assert any("Animation group" in error for error in errors)
    assert any("Negative X errors" in error for error in errors)


def test_log_axes_reject_nonpositive_data():
    options = normalize_scatter_options({"x": "Negative", "log_x": True}, sample_frame())
    assert any("positive values" in error for error in validate_scatter_options(options, sample_frame()))
