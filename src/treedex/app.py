import dash
from .layouts.main_layout import make_layout
from .callbacks import register_callbacks

"""
Dash application factory for Treedex.

This module is responsible for creating and configuring the Dash app.
It wires together the layout and the callbacks, but does not deal with
data loading or command-line argument parsing.

This separation allows:
- Easier testing
- Cleaner main entry point
- Future support for multi-page or modular dashboards
"""

def create_app(df_table, f_tree):
    """
    Create and configure the Dash application.

    Parameters
    ----------
    df_table : pandas.DataFrame
        DataFrame containing species or metadata used across the dashboard
        (tables, plots, filters, etc.).

    f_tree : plotly.graph_objects.Figure
        Plotly figure representing the phylogenetic tree, typically exported
        from ETE4 using the Dash backend.

    Returns
    -------
    dash.Dash
        A fully configured Dash application instance ready to be run.
    """
    # Initialize Dash application
    app = dash.Dash(__name__)
    # Build and assign the main layout
    app.layout = make_layout(df_table, f_tree)
    # Register all Dash callbacks (interactivity logic)
    register_callbacks(app, df_table, df_table)

    return app