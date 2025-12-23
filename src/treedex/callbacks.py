# callbacks.py
from dash import Input, Output
from treedex.components.plots import make_scatter_plot  # importing function

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
