"""Table-backed controls and validation for every Plotly Express pie argument."""

from copy import deepcopy
import json
import math
from numbers import Real

import pandas as pd
import plotly.express as px


DEFAULT_PIE_OPTIONS = {
    "names": None, "values": None, "color": None,
    "facet_row": None, "facet_col": None, "facet_col_wrap": 0,
    "facet_row_spacing": None, "facet_col_spacing": None,
    "color_discrete_palette": "Plotly", "color_discrete_sequence": None,
    "color_discrete_map": None, "hover_name": None, "hover_data": [],
    "hover_data_format": None, "custom_data": [], "category_orders": None,
    "labels": None, "title": "Pie chart", "subtitle": None,
    "template": "plotly_white", "width": None, "height": None,
    "opacity": 1.0, "hole": 0.0,
}
COLUMN_OPTIONS = {"names", "values", "color", "facet_row", "facet_col", "hover_name"}
JSON_OPTIONS = {
    "color_discrete_sequence": list, "color_discrete_map": dict,
    "hover_data_format": dict, "category_orders": dict, "labels": dict,
}


def normalize_pie_options(options, frame):
    normalized = deepcopy(DEFAULT_PIE_OPTIONS)
    normalized.update({k: v for k, v in (options or {}).items() if k in normalized})
    for name in COLUMN_OPTIONS:
        if normalized[name] not in frame.columns:
            normalized[name] = None
    if normalized["names"] is None and len(frame.columns):
        normalized["names"] = "Species" if "Species" in frame else frame.columns[0]
    if normalized["values"] not in frame.select_dtypes(include="number").columns:
        normalized["values"] = None
    for name in ("hover_data", "custom_data"):
        normalized[name] = [col for col in (normalized[name] or []) if col in frame]
    return normalized


def pie_kwargs(options):
    """Decode structured inputs and map UI helpers onto px.pie arguments."""
    kwargs = {k: v for k, v in options.items() if k in DEFAULT_PIE_OPTIONS}
    palette = kwargs.pop("color_discrete_palette", "Plotly")
    for name, expected in JSON_OPTIONS.items():
        value = kwargs.get(name)
        if value is None or value == "":
            kwargs[name] = None
            continue
        if name == "color_discrete_map" and value == "identity":
            continue
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError as exc:
                raise ValueError(f"{name.replace('_', ' ').capitalize()} must be valid JSON.") from exc
        if not isinstance(value, expected):
            raise ValueError(f"{name.replace('_', ' ').capitalize()} must be a JSON {'array' if expected is list else 'object'}.")
        kwargs[name] = value
    sequence = kwargs.get("color_discrete_sequence")
    if sequence is not None and (not sequence or not all(isinstance(v, str) for v in sequence)):
        raise ValueError("Custom colors must be a nonempty JSON array of CSS colors.")
    if sequence is None:
        kwargs["color_discrete_sequence"] = getattr(px.colors.qualitative, palette, None)
    color_map = kwargs.get("color_discrete_map")
    if isinstance(color_map, dict) and not all(isinstance(v, str) for v in color_map.values()):
        raise ValueError("Color map values must be CSS color strings.")
    if not all(isinstance(v, list) for v in (kwargs.get("category_orders") or {}).values()):
        raise ValueError("Category order values must be JSON arrays.")
    if not all(isinstance(v, str) for v in (kwargs.get("labels") or {}).values()):
        raise ValueError("Label values must be strings.")
    hover_format = kwargs.pop("hover_data_format")
    if hover_format is not None:
        if not all(isinstance(v, (bool, str)) for v in hover_format.values()):
            raise ValueError("Hover format values must be true, false, or formatting strings.")
        kwargs["hover_data"] = {**{col: True for col in (kwargs.get("hover_data") or [])}, **hover_format}
    else:
        kwargs["hover_data"] = kwargs.get("hover_data") or None
    kwargs["custom_data"] = kwargs.get("custom_data") or None
    kwargs["facet_col_wrap"] = kwargs.get("facet_col_wrap") or 0
    return kwargs


def validate_pie_options(options, frame):
    errors = []
    if frame.empty:
        errors.append("The current data contains no rows.")
    if not options.get("names"):
        errors.append("Choose a slice names column.")
    values_column = options.get("values")
    if values_column in frame:
        values = pd.to_numeric(frame[values_column], errors="coerce")
        if not values.map(lambda v: pd.notna(v) and math.isfinite(v) and v >= 0).all() or not values.gt(0).any():
            errors.append("Slice values must be finite, nonnegative numbers with at least one positive value.")
    for name in ("opacity", "hole", "facet_row_spacing", "facet_col_spacing"):
        value = options.get(name)
        if value is not None and (not isinstance(value, Real) or not math.isfinite(value) or not 0 <= value <= 1):
            errors.append(f"{name.replace('_', ' ').capitalize()} must be between 0 and 1.")
    for name, minimum in (("facet_col_wrap", 0), ("width", 10), ("height", 10)):
        value = options.get(name)
        if value is not None and (not isinstance(value, Real) or not math.isfinite(value) or value < minimum or int(value) != value):
            errors.append(f"{name.replace('_', ' ').capitalize()} must be a whole number of at least {minimum}.")
    if options.get("facet_row") and options.get("facet_col_wrap"):
        errors.append("Facet column wrap cannot be used together with row facets.")
    try:
        kwargs = pie_kwargs(options)
        for name in ("category_orders", "labels"):
            unknown = set(kwargs.get(name) or {}) - set(frame.columns)
            if unknown:
                errors.append(f"{name.replace('_', ' ').capitalize()} contains unknown columns: {', '.join(sorted(unknown))}.")
        if isinstance(kwargs.get("hover_data"), dict):
            unknown = set(kwargs["hover_data"]) - set(frame.columns)
            if unknown:
                errors.append(f"Hover formats contain unknown columns: {', '.join(sorted(unknown))}.")
    except ValueError as exc:
        errors.append(str(exc))
    return errors
