"""Build pie figures while retaining species membership for linked selection."""

import plotly.express as px

from ..pie_options import pie_kwargs


def make_pie_plot(frame, selected_species=None, **options):
    kwargs = pie_kwargs(options)
    custom_columns = list(kwargs.get("custom_data") or [])
    if "Species" in frame and "Species" not in custom_columns:
        custom_columns.append("Species")
    kwargs["custom_data"] = custom_columns or None
    color = kwargs.get("color")
    # Plotly 6.5's pie path calls .copy() on this documented string mode.
    if kwargs.get("color_discrete_map") == "identity":
        kwargs["color_discrete_map"] = {value: value for value in frame[color].dropna().unique()} if color else {}
    # Its pie color path also calls .append() on hover_data, even for dicts.
    # Let Express construct the colors separately, preserving its palette/order
    # semantics while the main figure retains formatted or hidden hover fields.
    if color and isinstance(kwargs.get("hover_data"), dict):
        kwargs["hover_data"].setdefault(color, True)
        colored = px.pie(data_frame=frame, **{**kwargs, "hover_data": list(kwargs["hover_data"])})
        figure = px.pie(data_frame=frame, **{**kwargs, "color": None})
        for trace, colored_trace in zip(figure.data, colored.data):
            trace.marker.colors = colored_trace.marker.colors
    else:
        figure = px.pie(data_frame=frame, **kwargs)
    selected = {str(name).casefold() for name in (selected_species or [])}
    for trace in figure.data:
        membership = {}
        if "Species" in custom_columns and trace.customdata is not None:
            species_index = custom_columns.index("Species")
            for label, row in zip(trace.labels, trace.customdata):
                membership.setdefault(str(label), []).append(str(row[species_index]))
        trace.meta = {"species_by_label": membership}
        trace.pull = [
            0.08 if any(name.casefold() in selected for name in membership.get(str(label), [])) else 0
            for label in trace.labels
        ]
    return figure.update_layout(clickmode="event", uirevision="pie")
