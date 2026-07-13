from dash import html, dcc

"""
Layout component for the phylogenetic tree panel.

This module defines the left-side layout that displays the phylogenetic
tree exported from ETE4. The tree is considered mandatory and is always
visible in the application.
"""

def tree_layout(f_tree):
    """
    Create the tree panel layout.

    Parameters
    ----------
    f_tree : plotly.graph_objects.Figure
        Plotly figure representing the phylogenetic tree.

    Returns
    -------
    dash.html.Div
        A Div containing the tree visualization.
    """

    return html.Div(
        children=[
            html.H2(
                style={
                    'textAlign': 'center',
                    'padding': '10px'
                }
            ),

            # Phylogenetic tree rendered as a Plotly figure
            dcc.Graph(
                id="tree-graph",
                figure=f_tree,
                config={"responsive": True},
                style={'height': '85%'},
            )
        ],
        style={
            'width': '35%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '5px',
            'borderRight': '1px solid #ccc',
            'height': '700px',
        }
    )
