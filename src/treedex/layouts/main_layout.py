from dash import html
from .tree_layout import tree_layout
from .dashboard_layout import dashboard_layout

"""
Main application layout.

This module composes the full page layout by combining the tree panel
and the dashboard panel.
"""

def make_layout(df_table, f_tree):
    """
    Build the main application layout.

    Parameters
    ----------
    df_table : pandas.DataFrame
        Table data used across the dashboard.
    f_tree : plotly.graph_objects.Figure
        Phylogenetic tree figure.

    Returns
    -------
    dash.html.Div
        The root layout container.
    """

    return html.Div(
        children=[
            tree_layout(f_tree),
            dashboard_layout(df_table)
        ]
    )
