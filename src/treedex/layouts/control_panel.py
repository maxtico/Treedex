from dash import dcc, html

from ete4.dashview import DEFAULT_SHAPE, normalize_shape


def _shape_button(shape, selected_shape):
    selected = shape == selected_shape
    class_name = "tree-shape-button"
    if selected:
        class_name += " is-selected"

    return html.Button(
        shape.capitalize(),
        id=f"tree-shape-{shape}",
        className=class_name,
        type="button",
        **{"aria-pressed": str(selected).lower()},
    )


def _brand():
    """Compact TreeDEx wordmark built from accessible HTML and CSS."""
    return html.Div(
        [
            html.Span(
                [
                    html.Span(className="treedex-logo__branch treedex-logo__branch--left"),
                    html.Span(className="treedex-logo__branch treedex-logo__branch--right"),
                    html.Span(className="treedex-logo__trunk"),
                ],
                className="treedex-logo__mark",
                **{"aria-hidden": "true"},
            ),
            html.Span(
                [html.Span("Tree", className="treedex-logo__accent"), "DEx"],
                className="treedex-logo__name",
            ),
        ],
        className="treedex-logo",
        **{"aria-label": "TreeDEx"},
    )


def _tree_panel(initial_shape):
    return html.Div(
        [
            html.Div(
                [
                    html.Span("Tree layout", className="control-panel__title"),
                    html.Span(
                        "Choose how the phylogeny is displayed",
                        className="control-panel__description",
                    ),
                ],
                className="control-panel__heading",
            ),
            html.Div(
                [
                    html.Span("Shape", className="tree-control__label"),
                    html.Div(
                        [
                            _shape_button("rectangular", initial_shape),
                            _shape_button("circular", initial_shape),
                        ],
                        className="tree-shape-options",
                        role="group",
                        **{"aria-label": "Tree shape"},
                    ),
                ],
                className="tree-control",
            ),
        ],
        className="control-panel__content",
    )


def _plot_type_label(name, asset=None, symbol=None):
    visual = (
        html.Img(src=asset, alt="", className="plot-type-option__image")
        if asset
        else html.Span(symbol, className="plot-type-option__symbol", **{"aria-hidden": "true"})
    )
    return html.Div(
        [visual, html.Span(name, className="plot-type-option__name")],
        className="plot-type-option",
    )


def _plots_panel():
    """Plot selection controls; type-specific options are added later."""
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Current plot", htmlFor="current-plot-selector", className="plot-control__label"),
                            dcc.Dropdown(
                                id="current-plot-selector",
                                options=[{"label": "plot_1", "value": "plot_1"}],
                                value="plot_1",
                                clearable=False,
                                searchable=False,
                                className="plot-control__dropdown",
                            ),
                        ],
                        className="plot-control",
                    ),
                    html.Div(
                        [
                            html.Label("Plot type", htmlFor="plot-type-selector", className="plot-control__label"),
                            dcc.Dropdown(
                                id="plot-type-selector",
                                options=[
                                    {
                                        "label": _plot_type_label(
                                            "Scatter plot",
                                            asset="/assets/scatter.svg",
                                        ),
                                        "value": "scatter",
                                    },
                                    {
                                        "label": _plot_type_label("Pie chart", symbol="◔"),
                                        "value": "pie",
                                    },
                                    {
                                        "label": _plot_type_label("Violin plot", symbol="⌁"),
                                        "value": "violin",
                                    },
                                ],
                                value=None,
                                placeholder="Select a plot type",
                                clearable=False,
                                searchable=False,
                                className="plot-control__dropdown plot-type-dropdown",
                            ),
                        ],
                        className="plot-control",
                    ),
                ],
                className="plot-controls-column",
            ),
            html.Div(
                [
                    html.Span("Plot options", className="plot-control__label"),
                    html.Span(
                        "Choose a plot type to configure it",
                        className="plot-options-placeholder",
                    ),
                ],
                id="plot-options-container",
                className="plot-control plot-control--options",
            ),
        ],
        className="control-panel__content plots-panel",
    )


def _coming_soon_panel(title, description, action_label=None):
    children = [
        html.Div(
            [
                html.Span(title, className="control-panel__title"),
                html.Span(description, className="control-panel__description"),
            ],
            className="control-panel__heading",
        )
    ]
    if action_label:
        children.append(
            html.Button(
                [html.Span("+", **{"aria-hidden": "true"}), action_label],
                className="control-panel__placeholder-action",
                type="button",
                disabled=True,
                title="Coming soon",
            )
        )
    children.append(html.Span("Coming soon", className="control-panel__badge"))
    return html.Div(children, className="control-panel__content")



def _data_panel():
    """Controls for uploading a replacement data table."""
    return html.Div(
        [
            html.Div(
                [
                    html.Span("Data", className="control-panel__title"),
                    html.Span(
                        "Manage the data connected to this dashboard",
                        className="control-panel__description",
                    ),
                ],
                className="control-panel__heading",
            ),
            dcc.Upload(
                id="upload-data",
                children=html.Div(
                    [
                        html.Span("+", **{"aria-hidden": "true"}),
                        html.Span(" Upload data"),
                    ]
                ),
                multiple=False,
                className="control-panel__placeholder-action",
                accept=".csv,.tsv,.txt",
            ),
            html.Div(
                "Accepted formats: CSV, TSV and TXT",
                id="upload-data-status",
                className="control-panel__description",
            ),
        ],
        className="control-panel__content",
    )

def top_control_panel(initial_shape=DEFAULT_SHAPE):
    """Return the main TreeDEx navigation and contextual controls."""
    initial_shape = normalize_shape(initial_shape)
    return html.Header(
        html.Div(
            [
                _brand(),
                dcc.Tabs(
                    id="control-panel-tabs",
                    value="tree",
                    className="control-tabs",
                    parent_className="control-tabs-container",
                    content_className="control-tabs__content",
                    children=[
                        dcc.Tab(
                            _tree_panel(initial_shape),
                            label="Tree",
                            value="tree",
                            className="control-tab",
                            selected_className="control-tab--selected",
                        ),
                        dcc.Tab(
                            _plots_panel(),
                            label="Plots",
                            value="plots",
                            className="control-tab",
                            selected_className="control-tab--selected",
                        ),
                        dcc.Tab(
                            _data_panel(),
                            label="Data",
                            value="data",
                            className="control-tab",
                            selected_className="control-tab--selected",
                        ),
                    ],
                ),
                html.Button(
                    "×",
                    id="control-panel-close",
                    className="control-panel__close",
                    type="button",
                    title="Close plot controls",
                    **{"aria-label": "Close plot controls"},
                ),
            ],
            className="control-bar__inner",
        ),
        id="top-control-panel",
        className="control-bar",
    )
