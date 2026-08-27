# callbacks.py
import base64
import io

import pandas as pd
from dash import Input, Output, State, ctx, dcc, html, no_update
from .components.plots import make_scatter_plot, scatter_config

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


    def scatter_columns(table_data):
        """Return the current data frame and sensible numeric axis defaults."""
        current_df = pd.DataFrame(table_data) if table_data else df_scatter.copy()
        numeric_cols = current_df.select_dtypes(include="number").columns.tolist()
        default_x = "X" if "X" in numeric_cols else (numeric_cols[0] if numeric_cols else None)
        default_y = "Y" if "Y" in numeric_cols else (
            numeric_cols[1] if len(numeric_cols) > 1 else default_x
        )
        return current_df, numeric_cols, default_x, default_y

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
        Input("scatter-plot", "clickData", allow_optional=True),
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
        Output("plot-options-container", "children"),
        Input("plot-type-selector", "value"),
        Input("species-table", "data"),
    )
    def show_plot_options(plot_type, table_data):
        """Render controls for the plot type selected by the user."""
        label = html.Span("Plot options", className="plot-control__label")

        if plot_type != "scatter":
            message = (
                "Choose a plot type to configure it"
                if not plot_type
                else "Options for this plot type are coming soon"
            )
            return [
                label,
                html.Span(message, className="plot-options-placeholder"),
            ]

        current_df, numeric_cols, default_x, default_y = scatter_columns(table_data)
        if not numeric_cols:
            return [
                label,
                html.Span(
                    "The current data needs at least one numeric column.",
                    className="plot-options-placeholder",
                ),
            ]

        axis_options = [{"label": col, "value": col} for col in numeric_cols]
        column_options = [
            {"label": str(col), "value": col}
            for col in current_df.columns
        ]
        size_columns = []
        for col in numeric_cols:
            values = pd.to_numeric(current_df[col], errors="coerce").dropna()
            if not values.empty and values.ge(0).all() and values.gt(0).any():
                size_columns.append(col)
        size_options = [{"label": col, "value": col} for col in size_columns]

        def optional_dropdown(component_id, options):
            return dcc.Dropdown(
                id=component_id,
                options=options,
                value=None,
                placeholder="None",
                clearable=True,
                className="scatter-option__dropdown",
            )

        return [
            label,
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("X axis", htmlFor="scatter-x-axis"),
                            dcc.Dropdown(
                                id="scatter-x-axis",
                                options=axis_options,
                                value=default_x,
                                clearable=False,
                                className="scatter-option__dropdown",
                            ),
                        ],
                        className="scatter-option",
                    ),
                    html.Div(
                        [
                            html.Label("Y axis", htmlFor="scatter-y-axis"),
                            dcc.Dropdown(
                                id="scatter-y-axis",
                                options=axis_options,
                                value=default_y,
                                clearable=False,
                                className="scatter-option__dropdown",
                            ),
                        ],
                        className="scatter-option",
                    ),
                    html.Div(
                        [
                            html.Label("Color by", htmlFor="scatter-color-by"),
                            optional_dropdown("scatter-color-by", column_options),
                        ],
                        className="scatter-option",
                    ),
                    html.Div(
                        [
                            html.Label("Size by", htmlFor="scatter-size-by"),
                            optional_dropdown("scatter-size-by", size_options),
                        ],
                        className="scatter-option",
                    ),
                    html.Div(
                        [
                            html.Label("Text", htmlFor="scatter-text-by"),
                            optional_dropdown("scatter-text-by", column_options),
                        ],
                        className="scatter-option scatter-option--text",
                    ),
                    html.Div(
                        [
                            html.Label("Plot title", htmlFor="scatter-plot-title"),
                            dcc.Input(
                                id="scatter-plot-title",
                                type="text",
                                value="Scatter plot",
                                placeholder="Enter a title",
                                className="scatter-option__input",
                            ),
                        ],
                        className="scatter-option scatter-option--title",
                    ),
                    html.Button(
                        "Build plot",
                        id="build-scatter-plot",
                        n_clicks=0,
                        type="button",
                        className="build-plot-button",
                    ),
                ],
                className="scatter-options",
            ),
        ]

    @app.callback(
        Output("main-plot-area", "children"),
        Input("build-scatter-plot", "n_clicks", allow_optional=True),
        Input("selected-species", "data"),
        State("scatter-x-axis", "value", allow_optional=True),
        State("scatter-y-axis", "value", allow_optional=True),
        State("scatter-plot-title", "value", allow_optional=True),
        State("scatter-color-by", "value", allow_optional=True),
        State("scatter-size-by", "value", allow_optional=True),
        State("scatter-text-by", "value", allow_optional=True),
        State("species-table", "data"),
        prevent_initial_call=True,
    )
    def build_scatter_plot(
        n_clicks,
        selected_species,
        x_value,
        y_value,
        title_value,
        color_value,
        size_value,
        text_value,
        table_data,
    ):
        """Build the configured scatter plot and keep its selection highlighted."""
        if not n_clicks:
            return no_update

        current_df, _, default_x, default_y = scatter_columns(table_data)
        x_axis = x_value if x_value in current_df.columns else default_x
        y_axis = y_value if y_value in current_df.columns else default_y
        color_column = color_value if color_value in current_df.columns else None
        size_column = size_value if size_value in current_df.columns else None
        text_column = text_value if text_value in current_df.columns else None
        if x_axis is None or y_axis is None:
            return no_update

        selected_lookup = {
            str(name).casefold() for name in (selected_species or [])
        }
        selection_idx = [
            index
            for index, name in enumerate(current_df["Species"])
            if str(name).casefold() in selected_lookup
        ]
        figure = make_scatter_plot(
            current_df,
            x=x_axis,
            y=y_axis,
            title=title_value or "Scatter plot",
            selection=selection_idx,
            color=color_column,
            size=size_column,
            text=text_column,
        )
        return html.Div(
            dcc.Graph(
                id="scatter-plot",
                figure=figure,
                config={**scatter_config, "responsive": True},
                className="dashboard-scatter-plot",
            ),
            className="dashboard-plot-card",
        )

    @app.callback(
        Output("control-panel-tabs", "value"),
        Output("top-control-panel", "className"),
        Input("add-plot-btn", "n_clicks", allow_optional=True),
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
