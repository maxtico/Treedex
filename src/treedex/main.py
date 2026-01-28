import dash
from dash import dcc, html, dash_table
import pandas as pd
import plotly.express as px
import argparse
import sys
from pathlib import Path
import ete4.dashview.dasher  # aplica el patch
from ete4 import PhyloTree

# Importem les nostres funcions modulars
from treedex.components.plots import make_scatter_plot, make_scatter_combo
from treedex.callbacks import register_callbacks

# Aqui tenim una funció per parsejar arguments de línia de comandes
def parse_args():
    parser = argparse.ArgumentParser(
        description="Treedex dashboard"
    )
    parser.add_argument(
        "-d", "--data",
        required=True,
        help="Path to species information CSV file"
    )
    parser.add_argument(
        "-t", "--tree",
        required=False,
        help="Path to Newick tree file"
    )
    return parser.parse_args()


def main():

    # Reading the data
    args = parse_args()
    data_path = Path(args.data)
    tree_path = args.tree

    if not data_path.exists():
        print(f"ERROR: File not found: {data_path}")
        sys.exit(1)

    # Reading input
    df_table = pd.read_csv(data_path)
    t = PhyloTree(tree_path)

    # Exporting the tree
    f_tree = t.dash(export=True)

    # Initialize Dash app
    app = dash.Dash(__name__)

    # Layout
    app.layout = html.Div([

        # Left column: Tree + Table
        html.Div([
            html.H2("Tree", style={'textAlign': 'center', 'padding': '10px'}),

            # Okay this is running but not ideal, because it requires to run ete4 separately. We should run it from the main code and call the server.
            # To run ete4: ete4 explore -t ../../mammal_tree.nw
            dcc.Graph(figure=f_tree),

            dash_table.DataTable(
                id="species-table",
                columns=[{"name": col, "id": col} for col in df_table.columns],
                data=df_table.to_dict("records"),
                row_selectable="multi",
                style_cell={'textAlign': 'center'}
            )

        ], style={
            'width': '25%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '10px',
            'borderRight': '1px solid #ccc'
        }),

        # Right column: Scatter + Pie
        html.Div([

            # Scatter created with your custom plot function
            dcc.Graph(
                id='scatter-plot',
                figure=make_scatter_plot(
                    dfr=df_table,
                    x="X",
                    y="Y",
                    title="Demo Scatter Plot",
                    selection=[]
                )
            ),

        ], style={
            'width': '70%',
            'display': 'inline-block',
            'padding': '10px',
            'verticalAlign': 'top'
        })

    ])

    # Registrem els callbacks modularment
    register_callbacks(app, df_table, df_table)

    # Run server
    app.run(debug=True)

if __name__ == '__main__':
    main()

