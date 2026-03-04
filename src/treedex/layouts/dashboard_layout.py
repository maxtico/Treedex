from dash import html, dcc, dash_table
from ..components.plots import make_scatter_plot

"""
Layout component for the main dashboard panel.

This module defines the right-side layout of the application, which
contains the species table and the main data visualizations (e.g.
scatter plots). The content of this panel may become dynamic in the
future (home screen, plot selector, etc.).
"""

def create_home_panel(df_table):
    """
    Home panel with a single plot button + SVG image.
    """
    return html.Div(
        children=[
            html.H4("Select a plot to display",
                style={
                    'textAlign': 'center',       # Centrat
                    'fontSize': '24px',          # Més gran
                    'marginBottom': '30px'       # Espai per sota
                }),
            html.Div(
                children=[
                    html.Button(
                        children=[
                            html.Img(
                                src="/assets/scatter.svg",  # <- Path dins /assets
                                style={'width': '150px', 'height': '100px'}
                            ),
                            html.Div(
                                "Scatter Plot",
                                style={
                                    'textAlign': 'center',
                                    'paddingTop': '2px',
                                    'fontSize': '18px',      # Nom més gran
                                    'fontWeight': 'bold',
                                }
                            )
                        ],
                        id="scatter-btn",
                        className="scatter-btn",
                        style={
                            'border': '#0080ff solid 1px',
                            'background': '#F9F9F9',
                            'cursor': 'pointer',
                            'padding': '1px 1px'
                        }
                    )
                ],
                style={
                    'width': '100%',
                    'display': 'flex',
                    'justifyContent': 'flex-start'
                }
            )
        ],
        style={
            'width': '100%',
            'display': 'block',
            'margin': '10px 0'
        }
    )

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

            html.Div(
                id='main-plot-area',
                children=[
                    create_home_panel(df_table)  # al principi només el botó
                ],
                style={'flex': '1 1 auto'}
            ),
            # Species / metadata table
            dash_table.DataTable(
                id="species-table",
                columns=[{"name": col, "id": col} for col in df_table.columns],
                data=df_table.to_dict("records"),
                row_selectable="multi",
                style_cell={'textAlign': 'center'}
            )

        ],
        style={
            'width': '60%',
            'display': 'inline-flex',
            'flexDirection': 'column',
            'padding': '10px',
            'verticalAlign': 'top',
            'height': '680px'
        }
    )
