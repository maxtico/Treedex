# callbacks.py
import dash
from dash import Input, Output, State, ctx, dcc, html, no_update
from .components.plots import make_scatter_plot, make_scatter_menu  # importing function

def register_callbacks(app, df_table, df_scatter):

    numeric_cols = df_scatter.select_dtypes(include="number").columns.tolist()
    default_x = "X" if "X" in df_scatter.columns else (numeric_cols[0] if numeric_cols else None)
    default_y = "Y" if "Y" in df_scatter.columns else (numeric_cols[1] if len(numeric_cols) > 1 else default_x)

    axis_options = [{"label": col, "value": col} for col in numeric_cols]

    species = df_table["Species"].astype(str).tolist()

    def canonical_species(names):
        """Return valid table species, preserving table order."""
        requested = {
            str(name).casefold()
            for name in (names or [])
            if name is not None
        }
        return [
            name
            for name in species
            if name.casefold() in requested
        ]

    @app.callback(
        Output("selected-species", "data"),
        Output("species-table", "selected_rows"),
        Input("tree-graph", "clickData"),
        Input("scatter-plot", "clickData"),
        Input("species-table", "selected_rows"),
        State("selected-species", "data"),
        prevent_initial_call=True,
    )
    def synchronize_selection(tree_click, scatter_click, selected_rows, current):
        """Keep tree, scatter and table selections in one shared state."""
        trigger = ctx.triggered_id

        if trigger == "species-table":
            selected = [
                species[index]
                for index in (selected_rows or [])
                if 0 <= index < len(species)
            ]
            selected = canonical_species(selected)
            if selected == canonical_species(current):
                return no_update, no_update
            return selected, no_update

        if trigger == "scatter-plot":
            point = (scatter_click or {}).get("points", [{}])[0]
            customdata = point.get("customdata")
            clicked_name = (
                customdata[0]
                if isinstance(customdata, (list, tuple)) and customdata
                else point.get("hovertext") or point.get("text")
            )
            selected = canonical_species([clicked_name])

        elif trigger == "tree-graph":
            point = (tree_click or {}).get("points", [{}])[0]
            node = point.get("customdata") or {}
            if not isinstance(node, dict):
                return no_update, no_update
            selected = canonical_species(
                node.get("leaf_names") or [node.get("name")]
            )
        else:
            return no_update, no_update

        if not selected:
            return no_update, no_update

        selected_lookup = {name.casefold() for name in selected}
        rows = [
            index
            for index, name in enumerate(species)
            if name.casefold() in selected_lookup
        ]
        return selected, rows

    @app.callback(
        Output("scatter-plot", "figure"),
        Input("selected-species", "data"),
        Input({'type': 'scatter_dropdown', 'index': 1, 'property': 'dataset'}, "value"),
        Input({'type': 'scatter_dropdown', 'index': 1, 'property': 'x'}, "value"),
        Input({'type': 'scatter_dropdown', 'index': 1, 'property': 'y'}, "value"),
        Input({'type': 'scatter_inputtext', 'index': 1, 'property': 'title'}, "value"),
        prevent_initial_call=True
    )
    def highlight_scatter(selected_species, _dataset_value, x_value, y_value, title_value):
        """
        Highlight scatter plot points based on selected rows in the species table.
        """
        x_axis = x_value if x_value in df_scatter.columns else default_x
        y_axis = y_value if y_value in df_scatter.columns else default_y
        chart_title = title_value if title_value else "Demo Scatter Plot"

        if not selected_species:
            # No row selected, return default scatter plot
            return make_scatter_plot(df_scatter, x=x_axis, y=y_axis, title=chart_title, selection=[])

        # Mapping indexes of selected species in the scatter dataframe
        selected_lookup = {str(name).casefold() for name in selected_species}
        selection_idx = [
            i
            for i, name in enumerate(df_scatter["Species"])
            if str(name).casefold() in selected_lookup
        ]

        # Returning updated scatter plot with highlighted points
        return make_scatter_plot(df_scatter, x=x_axis, y=y_axis, title=chart_title, selection=selection_idx)

    # ---------------- Callback for the button click at SVG ----------------
    @app.callback(
        Output("main-plot-area", "children"),  # substitueix tot el div
        Input("scatter-btn", "n_clicks")
    )
    def show_scatter(n_clicks):
        """
        Replace the home panel with the scatter plot when the SVG button is clicked.
        """
        if n_clicks:
            return html.Div(
                children=[
                    make_scatter_menu(
                        1,
                        dataset_options=[{"label": "Current Table", "value": "current_table"}],
                        dataset_value="current_table",
                        x_options=axis_options,
                        x_value=default_x,
                        y_options=axis_options,
                        y_value=default_y,
                        title_value="Demo Scatter Plot"
                    ),
                    dcc.Graph(
                        id='scatter-plot',
                        figure=make_scatter_plot(
                            df_scatter,
                            x=default_x,
                            y=default_y,
                            title="Demo Scatter Plot",
                            selection=[]
                        ),
                        style={'height': 500}
                    )
                ]
            )
        return dash.no_update
