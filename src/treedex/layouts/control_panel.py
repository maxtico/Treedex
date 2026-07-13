from dash import html

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


def top_control_panel(initial_shape=DEFAULT_SHAPE):
    """Return the hover-activated control drawer shown above the dashboard."""
    initial_shape = normalize_shape(initial_shape)
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Treedex controls"),
                        ],
                        className="top-drawer__heading",
                        style={"display": "flex", "flexDirection": "column", "width": "100%"},
                    ),
                    html.Div(
                        [
                            html.Section(
                                [
                                    html.H3("Tree"),
                                    html.Div(
                                        [
                                            html.Span(
                                                "Shape",
                                                className="tree-control__label",
                                            ),
                                            html.Div(
                                                [
                                                    _shape_button(
                                                        "rectangular",
                                                        initial_shape,
                                                    ),
                                                    _shape_button(
                                                        "circular",
                                                        initial_shape,
                                                    ),
                                                ],
                                                className="tree-shape-options",
                                                role="group",
                                                **{"aria-label": "Tree shape"},
                                            ),
                                        ],
                                        className="tree-control",
                                    ),
                                ],
                                className="top-drawer__section",
                            ),
                            html.Section(
                                [
                                    html.H3("Dashboard"),
                                    html.P("Plot and data controls will appear here."),
                                ],
                                className="top-drawer__section",
                            ),
                        ],
                        className="top-drawer__sections",
                    ),
                ],
                className="top-drawer__body",
            ),
            html.Div(
                [
                    html.Span("Controls", className="top-drawer__handle-label"),
                    html.Span(
                        "⌄",
                        className="top-drawer__arrow top-drawer__arrow--closed",
                        **{"aria-hidden": "true"},
                    ),
                    html.Span(
                        "⌃",
                        className="top-drawer__arrow top-drawer__arrow--open",
                        **{"aria-hidden": "true"},
                    ),
                ],
                className="top-drawer__handle",
                title="Show Treedex controls",
                tabIndex=0,
                role="button",
                **{"aria-label": "Show Treedex controls"},
            ),
        ],
        id="top-control-panel",
        className="top-drawer",
    )
