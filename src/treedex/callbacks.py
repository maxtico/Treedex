# callbacks.py
from dash import Input, Output, dcc
from .components.plots import make_scatter_plot  # importing function

def register_callbacks(app, df_table, df_scatter):

    @app.callback(
        Output("scatter-plot", "figure"),
        Input("species-table", "selected_rows")
    )
    def highlight_scatter(selected_rows):
        """
        Highlight scatter plot points based on selected rows in the species table.
        """
        if selected_rows is None or len(selected_rows) == 0:
            # No row selected, return default scatter plot
            return make_scatter_plot(df_scatter, x="X", y="Y", title="Demo Scatter Plot", selection=[])

        # Getting selected species from the table
        selected_species = [df_table.iloc[i]["Species"] for i in selected_rows]

        # Mapping indexes of selected species in the scatter dataframe
        selection_idx = [i for i, s in enumerate(df_scatter["Species"]) if s in selected_species]

        # Returning updated scatter plot with highlighted points
        return make_scatter_plot(df_scatter, x="X", y="Y", title="Demo Scatter Plot", selection=selection_idx)

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
            return dcc.Graph(
                id='scatter-plot',
                figure=make_scatter_plot(
                    df_scatter,
                    x="X",
                    y="Y",
                    title="Demo Scatter Plot",
                    selection=[]
                ),
                style={'height': 500}
            )
        return dash.no_update