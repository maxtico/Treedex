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
                            _coming_soon_panel(
                                "Plots",
                                "Add and configure dashboard visualizations",
                                "Add plot",
                            ),
                            label="Plots",
                            value="plots",
                            className="control-tab",
                            selected_className="control-tab--selected",
                        ),
                        dcc.Tab(
                            _coming_soon_panel(
                                "Data",
                                "Manage the data connected to this dashboard",
                            ),
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
