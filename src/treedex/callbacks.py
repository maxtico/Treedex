# callbacks.py
import base64
import io

import pandas as pd
from dash import ALL, Input, Output, State, ctx, dcc, html, no_update
from .components.plots import make_scatter_plot, scatter_config
from .scatter_options import normalize_scatter_options, validate_scatter_options

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
        Output("plot-options-content", "children"),
        Output("scatter-options-store", "data"),
        Input("plot-type-selector", "value"),
        Input("species-table", "data"),
        Input("scatter-options-page", "data"),
        State("scatter-options-store", "data"),
    )
    def show_plot_options(plot_type, table_data, active_page, stored_options):
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
            ], stored_options

        current_df, numeric_cols, default_x, default_y = scatter_columns(table_data)
        if not numeric_cols:
            return [
                label,
                html.Span(
                    "The current data needs at least one numeric column.",
                    className="plot-options-placeholder",
                ),
            ], stored_options

        options = normalize_scatter_options(stored_options, current_df)
        active_page = active_page if active_page in (1, 2, 3, 4) else 1
        axis_options = [{"label": str(col), "value": col} for col in numeric_cols]
        column_options = [{"label": str(col), "value": col} for col in current_df.columns]
        size_columns = []
        for col in numeric_cols:
            values = pd.to_numeric(current_df[col], errors="coerce").dropna()
            if not values.empty and values.ge(0).all() and values.gt(0).any():
                size_columns.append(col)
        size_options = [{"label": col, "value": col} for col in size_columns]

        def control_id(name):
            return {"type": "scatter-option", "name": name}

        def dropdown(name, choices, clearable=True, multi=False, placeholder="None"):
            return dcc.Dropdown(
                id=control_id(name), options=choices, value=options.get(name),
                placeholder=placeholder, clearable=clearable, multi=multi,
                className="scatter-option__dropdown",
            )

        def number(name, placeholder=None, **kwargs):
            return dcc.Input(
                id=control_id(name), type="number", value=options.get(name),
                placeholder=placeholder, className="scatter-option__input", **kwargs,
            )

        def text_input(name, placeholder=None, input_type="text"):
            return dcc.Input(
                id=control_id(name), type=input_type, value=options.get(name),
                placeholder=placeholder, className="scatter-option__input",
            )

        def field(label_text, name, component):
            return html.Div(
                [html.Label(label_text), component],
                className="scatter-option",
            )

        none_choice = [{"label": "None", "value": ""}]
        marginal_choices = none_choice + [
            {"label": value.title(), "value": value}
            for value in ("rug", "box", "violin", "histogram")
        ]
        boolean_choices = [
            {"label": "Off", "value": False}, {"label": "On", "value": True}
        ]
        if active_page == 1:
            page_fields = [
                field("X axis", "x", dropdown("x", axis_options, clearable=False)),
                field("Y axis", "y", dropdown("y", axis_options, clearable=False)),
                field("Color by", "color", dropdown("color", column_options)),
                field("Symbol by", "symbol", dropdown("symbol", column_options)),
                field("Size by", "size", dropdown("size", size_options)),
                field("Text labels", "text", dropdown("text", column_options)),
                field("Hover title", "hover_name", dropdown("hover_name", column_options)),
                field("Extra hover data", "hover_data", dropdown(
                    "hover_data", column_options, multi=True, placeholder="Select columns"
                )),
                field("Title", "title", text_input("title", "Scatter plot")),
                field("Subtitle", "subtitle", text_input("subtitle", "Optional subtitle")),
                field("Template", "template", dropdown("template", [{"label": name, "value": name} for name in ("plotly_white", "plotly", "plotly_dark", "ggplot2", "seaborn", "simple_white", "none")], clearable=False)),
            ]
        elif active_page == 2:
            page_fields = [
                field("Facet rows", "facet_row", dropdown("facet_row", column_options)),
                field("Facet columns", "facet_col", dropdown("facet_col", column_options)),
                field("Facet column wrap", "facet_col_wrap", number("facet_col_wrap", min=0, step=1)),
                field("Row spacing", "facet_row_spacing", number("facet_row_spacing", min=0, max=1, step=0.01)),
                field("Column spacing", "facet_col_spacing", number("facet_col_spacing", min=0, max=1, step=0.01)),
                field("X error +", "error_x", dropdown("error_x", size_options)),
                field("X error −", "error_x_minus", dropdown("error_x_minus", size_options)),
                field("Y error +", "error_y", dropdown("error_y", size_options)),
                field("Y error −", "error_y_minus", dropdown("error_y_minus", size_options)),
                field("Animation frame", "animation_frame", dropdown("animation_frame", column_options)),
                field("Animation group", "animation_group", dropdown("animation_group", column_options)),
            ]
        elif active_page == 3:
            page_fields = [
                field("Opacity", "opacity", number("opacity", min=0, max=1, step=0.05)),
                field("Maximum size", "size_max", number("size_max", min=1, step=1)),
                field("Discrete palette", "color_discrete_palette", dropdown(
                    "color_discrete_palette",
                    [{"label": name, "value": name} for name in ("Plotly", "D3", "G10", "T10", "Alphabet", "Dark24", "Light24")],
                    clearable=False,
                )),
                field("Continuous scale", "color_continuous_scale", dropdown(
                    "color_continuous_scale",
                    [{"label": name, "value": name} for name in ("Viridis", "Plasma", "Inferno", "Magma", "Cividis", "Turbo", "RdBu", "Spectral")],
                    clearable=False,
                )),
                field("Color minimum", "range_color_min", number("range_color_min")),
                field("Color maximum", "range_color_max", number("range_color_max")),
                field("Color midpoint", "color_continuous_midpoint", number("color_continuous_midpoint")),
                field("X marginal", "marginal_x", dropdown("marginal_x", marginal_choices)),
                field("Y marginal", "marginal_y", dropdown("marginal_y", marginal_choices)),
                field("Render mode", "render_mode", dropdown(
                    "render_mode", [{"label": value.upper() if value != "auto" else "Auto", "value": value} for value in ("auto", "svg", "webgl")], clearable=False
                )),
            ]
        else:
            try:
                import statsmodels  # noqa: F401
                trendline_choices = none_choice + [
                    {"label": "OLS", "value": "ols"}, {"label": "LOWESS", "value": "lowess"}
                ]
            except ImportError:
                trendline_choices = none_choice
            page_fields = [
                field("Log X", "log_x", dropdown("log_x", boolean_choices, clearable=False)),
                field("Log Y", "log_y", dropdown("log_y", boolean_choices, clearable=False)),
                field("X minimum", "range_x_min", number("range_x_min")),
                field("X maximum", "range_x_max", number("range_x_max")),
                field("Y minimum", "range_y_min", number("range_y_min")),
                field("Y maximum", "range_y_max", number("range_y_max")),
                field("Orientation", "orientation", dropdown("orientation", none_choice + [{"label": "Vertical", "value": "v"}, {"label": "Horizontal", "value": "h"}])),
                field("Trendline", "trendline", dropdown("trendline", trendline_choices)),
                field("Trendline scope", "trendline_scope", dropdown("trendline_scope", [{"label": "Per trace", "value": "trace"}, {"label": "Overall", "value": "overall"}], clearable=False)),
                field("Trendline color", "trendline_color_override", text_input("trendline_color_override", "CSS color")),
            ]

        return [
            html.Div(
                [label, html.Div([
                    html.Div([
                        html.Button(
                            str(page), id={"type": "scatter-page-button", "page": page},
                            n_clicks=0, type="button",
                            className="scatter-page-button" + (" is-active" if page == active_page else ""),
                            **{"aria-label": f"Scatter options page {page}", "aria-pressed": str(page == active_page).lower()},
                        ) for page in range(1, 5)
                    ], className="scatter-pages", role="group", **{"aria-label": "Scatter option pages"}),
                ], className="scatter-options-actions")],
                className="scatter-options-header",
            ),
            html.Div(
                [
                    html.Div(
                        page_fields + [
                            html.Button(
                                "Build plot", id="build-scatter-plot", n_clicks=0,
                                type="button", className="build-plot-button",
                            ),
                        ],
                        className="scatter-options-page",
                    ),
                ],
                className="scatter-options",
            ),
        ], options

    @app.callback(
        Output("scatter-options-page", "data"),
        Input({"type": "scatter-page-button", "page": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def change_scatter_page(_clicks):
        triggered = ctx.triggered_id
        return triggered["page"] if isinstance(triggered, dict) else no_update

    @app.callback(
        Output("scatter-options-store", "data", allow_duplicate=True),
        Input({"type": "scatter-option", "name": ALL}, "value"),
        State({"type": "scatter-option", "name": ALL}, "id"),
        State("scatter-options-store", "data"),
        prevent_initial_call=True,
    )
    def save_scatter_options(values, ids, stored_options):
        updated = dict(stored_options or {})
        for component_id, value in zip(ids or [], values or []):
            if isinstance(component_id, dict):
                updated[component_id["name"]] = None if value == "" else value
        return updated

    @app.callback(
        Output("main-plot-area", "children"),
        Output("scatter-validation-message", "children"),
        Output("scatter-plot-built", "data"),
        Input("build-scatter-plot", "n_clicks", allow_optional=True),
        Input("selected-species", "data"),
        State("scatter-options-store", "data"),
        State("species-table", "data"),
        State("scatter-plot-built", "data"),
        prevent_initial_call=True,
    )
    def build_scatter_plot(
        n_clicks,
        selected_species,
        stored_options,
        table_data,
        plot_built,
    ):
        """Build the configured scatter plot and keep its selection highlighted."""
        if ctx.triggered_id == "build-scatter-plot":
            if not n_clicks:
                return no_update, no_update, no_update
        elif not plot_built:
            return no_update, no_update, no_update

        current_df, _, _, _ = scatter_columns(table_data)
        options = normalize_scatter_options(stored_options, current_df)
        errors = validate_scatter_options(options, current_df)
        if errors:
            return no_update, html.Ul([html.Li(error) for error in errors]), no_update

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
            selection=selection_idx,
            **options,
        )
        return html.Div(
            dcc.Graph(
                id="scatter-plot",
                figure=figure,
                config={**scatter_config, "responsive": True},
                responsive=True,
                className="dashboard-scatter-plot",
            ),
            className="dashboard-plot-card",
        ), "", True

    app.clientside_callback(
        """
        function(addClicks) {
            if (!addClicks) {
                return [dash_clientside.no_update, dash_clientside.no_update];
            }
            const panel = document.getElementById("top-control-panel");
            // Repeated clicks should still leave only one mouse-leave handler.
            panel.onmouseleave = function() {
                if (panel.contains(document.activeElement)) {
                    document.activeElement.blur();
                }
                dash_clientside.set_props("top-control-panel", {
                    className: "control-bar"
                });
                panel.onmouseleave = null;
            };
            return ["plots", "control-bar is-open"];
        }
        """,
        Output("control-panel-tabs", "value"),
        Output("top-control-panel", "className"),
        Input("add-plot-btn", "n_clicks", allow_optional=True),
        prevent_initial_call=True,
    )
