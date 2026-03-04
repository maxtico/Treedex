# callbacks.py
import dash
from dash import Input, Output, State, dcc, html
from .components.plots import make_scatter_plot, make_scatter_menu  # importing function

def register_callbacks(app, df_table, df_scatter):

    numeric_cols = df_scatter.select_dtypes(include="number").columns.tolist()
    default_x = "X" if "X" in df_scatter.columns else (numeric_cols[0] if numeric_cols else None)
    default_y = "Y" if "Y" in df_scatter.columns else (numeric_cols[1] if len(numeric_cols) > 1 else default_x)

    axis_options = [{"label": col, "value": col} for col in numeric_cols]

    @app.callback(
        Output("scatter-plot", "figure"),
        Input("species-table", "selected_rows"),
        Input({'type': 'scatter_configure_ok', 'index': 1}, "n_clicks"),
        State({'type': 'scatter_dropdown', 'index': 1, 'property': 'x'}, "value"),
        State({'type': 'scatter_dropdown', 'index': 1, 'property': 'y'}, "value"),
        State({'type': 'scatter_inputtext', 'index': 1, 'property': 'title'}, "value"),
        prevent_initial_call=True
    )
    def highlight_scatter(selected_rows, _apply_clicks, x_value, y_value, title_value):
        """
        Highlight scatter plot points based on selected rows in the species table.
        """
        x_axis = x_value if x_value in df_scatter.columns else default_x
        y_axis = y_value if y_value in df_scatter.columns else default_y
        chart_title = title_value if title_value else "Demo Scatter Plot"

        if selected_rows is None or len(selected_rows) == 0:
            # No row selected, return default scatter plot
            return make_scatter_plot(df_scatter, x=x_axis, y=y_axis, title=chart_title, selection=[])

        # Getting selected species from the table
        selected_species = [df_table.iloc[i]["Species"] for i in selected_rows]

        # Mapping indexes of selected species in the scatter dataframe
        selection_idx = [i for i, s in enumerate(df_scatter["Species"]) if s in selected_species]

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
                    html.Button(
                        "Configure Scatter",
                        id="scatter-config-btn",
                        className="scatter-btn",
                        style={
                            'marginBottom': '10px',
                            'padding': '6px 10px',
                            'border': '#0080ff solid 1px',
                            'background': '#F9F9F9',
                            'cursor': 'pointer',
                            'fontWeight': 'bold'
                        }
                    ),
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

    @app.callback(
        Output({'type': 'scatter_menu', 'index': 1}, "is_open"),
        Input("scatter-config-btn", "n_clicks"),
        Input({'type': 'scatter_configure_ok', 'index': 1}, "n_clicks"),
        State({'type': 'scatter_menu', 'index': 1}, "is_open"),
        prevent_initial_call=True
    )
    def toggle_scatter_menu(open_clicks, apply_clicks, is_open):
        trigger_id = dash.ctx.triggered_id
        if trigger_id == "scatter-config-btn" and open_clicks:
            return not is_open
        if trigger_id == {'type': 'scatter_configure_ok', 'index': 1} and apply_clicks:
            return False
        return is_open
