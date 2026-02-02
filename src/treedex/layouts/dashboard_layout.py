from dash import html, dcc, dash_table
from ..components.plots import make_scatter_plot

"""
Layout component for the main dashboard panel.

This module defines the right-side layout of the application, which
contains the species table and the main data visualizations (e.g.
scatter plots). The content of this panel may become dynamic in the
future (home screen, plot selector, etc.).
"""

def dashboard_layout(df_table):
    """
    Create the dashboard panel layout.

    Parameters
    ----------
    df_table : pandas.DataFrame
        DataFrame containing species or metadata displayed in the table
        and used to generate plots.

    Returns
    -------
    dash.html.Div
        A Div containing the species table and the scatter plot.
    """

    return html.Div(
        children=[

            # Species / metadata table
            dash_table.DataTable(
                id="species-table",
                columns=[{"name": col, "id": col} for col in df_table.columns],
                data=df_table.to_dict("records"),
                row_selectable="multi",
                style_cell={'textAlign': 'center'}
            ),

            # Scatter plot (default dashboard view)
            dcc.Graph(
                id='scatter-plot',
                figure=make_scatter_plot(
                    dfr=df_table,
                    x="X",
                    y="Y",
                    title="Demo Scatter Plot",
                    selection=[]
                )
            )
        ],
        style={
            'width': '60%',
            'display': 'inline-block',
            'padding': '10px',
            'verticalAlign': 'top'
        }
    )
