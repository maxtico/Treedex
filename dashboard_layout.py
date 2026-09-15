from dash import html, dash_table

"""
Layout component for the main dashboard panel.

This module defines the right-side layout of the application, which
contains the species table and the main data visualizations (e.g.
scatter plots). The content of this panel may become dynamic in the
future (home screen, plot selector, etc.).
"""


def create_home_panel():
    """Initial empty state from which users can add a plot."""
    return html.Div(
        html.Button(
            [
                html.Span("+", className="add-plot-card__icon", **{"aria-hidden": "true"}),
                html.Span("Add plot", className="add-plot-card__label"),
            ],
            id="add-plot-btn",
            className="add-plot-card",
            type="button",
            title="Open plot controls",
        ),
        className="dashboard-empty-state",
    )


def dashboard_layout(df_table):
    """Create the responsive dashboard panel layout."""

    return html.Div(
        children=[
            html.Div(
                id="main-plot-area",
                children=[create_home_panel()],
                className="main-plot-area",
            ),
            dash_table.DataTable(
                id="species-table",
                columns=[{"name": col, "id": col} for col in df_table.columns],
                data=df_table.to_dict("records"),
                row_selectable="multi",
                fixed_rows={"headers": True},
                style_table={
                    "height": "145px",
                    "overflowY": "auto",
                    "overflowX": "auto",
                    "flexShrink": "0",
                },
                style_cell={
                    "textAlign": "center",
                    "minWidth": "140px",
                    "width": "140px",
                    "maxWidth": "220px",
                    "height": "26px",
                    "padding": "0px 8px",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
                style_header={
                    "height": "36px",
                    "fontWeight": "600",
                },
            ),
        ],
        className="dashboard-panel",
    )
