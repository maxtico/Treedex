# callbacks.py
import base64
import io

import pandas as pd
from dash import Input, Output, State, ctx, no_update
from .components.plots import make_scatter_plot

def register_callbacks(app, df_table, df_scatter):

    @app.callback(
        Output("species-table", "data"),
        Output("species-table", "columns"),
        Output("species-table", "selected_rows", allow_duplicate=True),
        Output("selected-species", "data", allow_duplicate=True),
        Output("upload-data-status", "children"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        prevent_initial_call=True,
    )
    def upload_data(contents, filename):
        """Parse an uploaded CSV/TSV/TXT file and replace the table contents."""
        if not contents:
            return no_update, no_update, no_update, no_update, no_update

        try:
            _, encoded = contents.split(",", 1)
            decoded = base64.b64decode(encoded)
            text = decoded.decode("utf-8-sig")

            lower_name = (filename or "").lower()
            if lower_name.endswith(".tsv"):
                uploaded_df = pd.read_csv(io.StringIO(text), sep="\\t")
            elif lower_name.endswith(".csv"):
                uploaded_df = pd.read_csv(io.StringIO(text))
            elif lower_name.endswith(".txt"):
                uploaded_df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
            else:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    "Unsupported file type. Please upload CSV, TSV or TXT.",
                )

            uploaded_df.columns = [str(col).strip() for col in uploaded_df.columns]

            if uploaded_df.empty:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    "The uploaded file contains no rows.",
                )

            if "Species" not in uploaded_df.columns:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    "The uploaded file must contain a 'Species' column.",
                )

            columns = [
                {"name": str(col), "id": str(col)}
                for col in uploaded_df.columns
            ]

            return (
                uploaded_df.to_dict("records"),
                columns,
                [],
                [],
                f"Loaded {filename}: {len(uploaded_df)} rows × {len(uploaded_df.columns)} columns.",
            )

        except UnicodeDecodeError:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                "Could not read the file as UTF-8 text.",
            )
        except Exception as exc:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                f"Could not load {filename or 'the file'}: {exc}",
            )


    numeric_cols = df_scatter.select_dtypes(include="number").columns.tolist()
    default_x = "X" if "X" in df_scatter.columns else (numeric_cols[0] if numeric_cols else None)
    default_y = "Y" if "Y" in df_scatter.columns else (numeric_cols[1] if len(numeric_cols) > 1 else default_x)

    axis_options = [{"label": col, "value": col} for col in numeric_cols]

    def canonical_species(names, species):
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
        State("species-table", "data"),
        prevent_initial_call=True,
    )
    def synchronize_selection(tree_click, scatter_click, selected_rows, current, table_data):
        """Keep tree, scatter and table selections in one shared state."""
        trigger = ctx.triggered_id

        current_table = table_data or []
        species = [
            str(row.get("Species"))
            for row in current_table
            if row.get("Species") is not None
        ]

        if trigger == "species-table":
            selected = [
                species[index]
                for index in (selected_rows or [])
                if 0 <= index < len(species)
            ]
            selected = canonical_species(selected, species)
            if selected == canonical_species(current, species):
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
            selected = canonical_species([clicked_name], species)

        elif trigger == "tree-graph":
            point = (tree_click or {}).get("points", [{}])[0]
            node = point.get("customdata") or {}
            if not isinstance(node, dict):
                return no_update, no_update
            selected = canonical_species(
                node.get("leaf_names") or [node.get("name")],
                species,
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

    @app.callback(
        Output("control-panel-tabs", "value"),
        Output("top-control-panel", "className"),
        Input("add-plot-btn", "n_clicks"),
        Input("control-panel-close", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_plot_controls(add_clicks, close_clicks):
        """Open plot controls from the dashboard and close them on request."""
        if ctx.triggered_id == "add-plot-btn" and add_clicks:
            return "plots", "control-bar is-open"
        if ctx.triggered_id == "control-panel-close" and close_clicks:
            return no_update, "control-bar"
        return no_update, no_update
