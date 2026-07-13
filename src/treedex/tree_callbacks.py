from dash import Input, Output, State, ctx, no_update

from ete4.dashview import make_tree_view_config, normalize_shape, tree_to_plotly


SHAPE_BUTTON_CLASS = "tree-shape-button"
SELECTED_SHAPE_BUTTON_CLASS = "tree-shape-button is-selected"


def register_tree_callbacks(app, tree):
    """Connect Treedex's tree controls to ETE's view configuration."""

    @app.callback(
        Output("tree-view-config", "data"),
        Input("tree-shape-rectangular", "n_clicks"),
        Input("tree-shape-circular", "n_clicks"),
        State("tree-view-config", "data"),
        prevent_initial_call=True,
    )
    def select_tree_shape(rectangular_clicks, circular_clicks, config):
        shape_by_button = {
            "tree-shape-rectangular": "rectangular",
            "tree-shape-circular": "circular",
        }
        shape = shape_by_button.get(ctx.triggered_id)
        if shape is None:
            return no_update

        updated_config = dict(config or {})
        updated_config.update(make_tree_view_config(shape))
        return updated_config

    @app.callback(
        Output("tree-graph", "figure"),
        Output("tree-shape-rectangular", "className"),
        Output("tree-shape-circular", "className"),
        Output("tree-shape-rectangular", "aria-pressed"),
        Output("tree-shape-circular", "aria-pressed"),
        Input("tree-view-config", "data"),
    )
    def render_tree_shape(config):
        shape = normalize_shape((config or {}).get("shape"))
        rectangular_selected = shape == "rectangular"
        circular_selected = shape == "circular"

        return (
            tree_to_plotly(tree, shape=shape),
            SELECTED_SHAPE_BUTTON_CLASS
            if rectangular_selected
            else SHAPE_BUTTON_CLASS,
            SELECTED_SHAPE_BUTTON_CLASS
            if circular_selected
            else SHAPE_BUTTON_CLASS,
            str(rectangular_selected).lower(),
            str(circular_selected).lower(),
        )
