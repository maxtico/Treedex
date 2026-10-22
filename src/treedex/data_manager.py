"""Dataset operations shared by the manager UI and dashboard synchronization."""
import base64
import io
import json
import math
from copy import deepcopy

import pandas as pd
from pandas.api.types import is_bool_dtype, is_integer_dtype, is_numeric_dtype

TYPES = ("text", "integer", "number", "boolean", "datetime")
ROLES = ("variable", "identifier", "tree-key", "category", "measure")


def infer_type(series):
    if is_bool_dtype(series):
        return "boolean"
    if is_integer_dtype(series):
        return "integer"
    if is_numeric_dtype(series):
        return "number"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "text"


def records(frame):
    # Preserve floating-point precision while normalizing nullable scalars and dates.
    normalized = frame.astype(object).where(frame.notna(), None)
    def encode(value):
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value.item()
    return json.loads(json.dumps(normalized.to_dict("records"), default=encode, allow_nan=False))


def make_dataset(frame, name="Dataset"):
    frame = frame.copy()
    frame.columns = [str(c).strip() for c in frame.columns]
    if any(not c for c in frame.columns) or not frame.columns.is_unique:
        raise ValueError("Column names must be nonempty and unique.")
    return {
        "name": name, "records": records(frame),
        "columns": [{"id": c, "name": c, "dtype": infer_type(frame[c]),
                     "description": "", "role": "tree-key" if c == "Species" else "variable",
                     "units": "", "values": "{}", "visible": True, "position": i + 1}
                    for i, c in enumerate(frame.columns)],
        "primary_key": None, "tree_key": "Species" if "Species" in frame.columns else None,
    }


def parse_upload(contents, filename):
    extension = (filename or "").rsplit(".", 1)[-1].lower()
    if extension not in ("csv", "tsv", "txt"):
        raise ValueError("Upload a CSV, TSV or TXT file.")
    text = base64.b64decode(contents.split(",", 1)[1], validate=True).decode("utf-8-sig")
    frame = pd.read_csv(io.StringIO(text), sep={"csv": ",", "tsv": "\t", "txt": None}[extension],
                        **({"engine": "python"} if extension == "txt" else {}))
    if frame.empty:
        raise ValueError("The uploaded file contains no rows.")
    return make_dataset(frame, filename)


def convert(series, dtype):
    if dtype == "text":
        return series.astype("string")
    if dtype in ("integer", "number"):
        result = pd.to_numeric(series, errors="raise")
        if not result.dropna().map(math.isfinite).all():
            raise ValueError("Numeric values must be finite.")
        return result.astype("Int64" if dtype == "integer" else "Float64")
    if dtype == "boolean":
        lookup = {"true": True, "false": False, "1": True, "0": False}
        def boolean(value):
            if pd.isna(value):
                return pd.NA
            key = str(value).strip().lower()
            if key not in lookup:
                raise ValueError("Booleans must be true, false, 1 or 0.")
            return lookup[key]
        return series.map(boolean).astype("boolean")
    if dtype == "datetime":
        return pd.to_datetime(series, errors="raise", format="mixed")
    raise ValueError(f"Unsupported type: {dtype}.")


def dataset_frame(dataset):
    if not dataset:
        return pd.DataFrame()
    frame = pd.DataFrame(dataset["records"], columns=[c["name"] for c in dataset["columns"]])
    for col in dataset["columns"]:
        frame[col["name"]] = convert(frame[col["name"]], col["dtype"])
    return frame


def apply_columns(dataset, edits, primary_key, tree_key):
    """Validate a complete schema transaction before returning a new dataset."""
    if not dataset:
        raise ValueError("Upload a dataset first.")
    original = {c["id"]: c for c in dataset["columns"]}
    if len(edits) != len(original) or {c["id"] for c in edits} != set(original):
        raise ValueError("Every existing column must appear exactly once.")
    updated = deepcopy(dataset)
    columns = []
    frame = dataset_frame(dataset)
    converted = {}
    for edit in edits:
        col = {**original[edit["id"]], **edit}
        col["name"] = str(col.get("name") or "").strip()
        if not col["name"]:
            raise ValueError("Column names cannot be empty.")
        if col["role"] not in ROLES:
            raise ValueError("Choose a supported column role.")
        try:
            position = float(col["position"])
            if not position.is_integer() or position < 1:
                raise ValueError()
            col["position"] = int(position)
            converted[col["id"]] = convert(frame[original[col["id"]]["name"]], col["dtype"])
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError(f"{col['name']}: invalid type or position. {exc}") from exc
        col["visible"] = col.get("visible") in (True, "true", "True")
        columns.append(col)
    if len({c["name"] for c in columns}) != len(columns):
        raise ValueError("Column names must be unique.")
    if len({c["position"] for c in columns}) != len(columns):
        raise ValueError("Column positions must be unique.")
    for key in (primary_key, tree_key):
        if key and key not in original:
            raise ValueError("Choose an existing key column.")
    if primary_key:
        values = converted[primary_key]
        if values.isna().any() or not values.is_unique:
            raise ValueError("The primary identifier must be unique and contain no missing values.")
    species_column = next((c for c in columns if c["name"] == "Species"), None)
    if species_column and tree_key and species_column["id"] != tree_key:
        raise ValueError("Rename the existing Species column before assigning a different tree key; Species is reserved for the linked key in plots.")
    if tree_key and converted[tree_key].isna().any():
        raise ValueError("The tree key cannot contain missing values.")
    columns.sort(key=lambda c: c["position"])
    updated.update(columns=columns, primary_key=primary_key or None, tree_key=tree_key or None,
                   records=records(pd.DataFrame({c["name"]: converted[c["id"]] for c in columns})))
    return updated


def apply_metadata(dataset, edits):
    updated = deepcopy(dataset)
    by_id = {row["id"]: row for row in edits}
    for col in updated["columns"]:
        edit = by_id[col["id"]]
        definitions = edit.get("values") or "{}"
        if not isinstance(json.loads(definitions), dict):
            raise ValueError("Value definitions must be a JSON object, e.g. {\"0\": \"Absent\"}.")
        if edit.get("role") not in ROLES:
            raise ValueError("Choose a supported column role.")
        for key in ("description", "role", "units", "values"):
            col[key] = edit.get(key) or ("{}" if key == "values" else "")
    return updated


def dashboard_records(dataset):
    """Project the configured tree key into the legacy dashboard Species field."""
    if not dataset:
        return [], []
    data = deepcopy(dataset["records"])
    key = next((c["name"] for c in dataset["columns"] if c["id"] == dataset["tree_key"]), None)
    for row in data:
        row["Species"] = str(row[key]) if key else None
    names = [c["name"] for c in dataset["columns"]]
    if "Species" not in names:
        names.append("Species")
    return data, [{"name": c, "id": c} for c in names]


def preview(dataset, page=0, size=50, search="", sort=None):
    """Only return the requested page to the preview component."""
    if not dataset:
        return [], 0, 0
    frame = pd.DataFrame(dataset["records"], columns=[c["name"] for c in dataset["columns"]])
    if search:
        mask = pd.Series(False, index=frame.index)
        for col in frame:
            mask |= frame[col].astype("string").str.contains(search, case=False, regex=False, na=False)
        frame = frame[mask]
    if sort:
        frame = frame.sort_values([s["column_id"] for s in sort],
                                  ascending=[s["direction"] == "asc" for s in sort], kind="stable")
    total = len(frame)
    pages = max(1, math.ceil(total / size))
    start = min(max(page or 0, 0), pages - 1) * size
    return records(frame.iloc[start:start + size]), pages, total


def association(dataset, leaves):
    if not dataset:
        return "No dataset loaded."
    key = next((c["name"] for c in dataset["columns"] if c["id"] == dataset["tree_key"]), None)
    if not key:
        return "No tree key configured. Choose one in Columns to link rows to tree leaves."
    names = {str(n).casefold() for n in leaves}
    values = [str(row[key]).casefold() for row in dataset["records"] if row[key] is not None]
    matched = sum(v in names for v in values)
    return f"Tree key: {key} · {matched:,} / {len(dataset['records']):,} rows matched · {len(names - set(values)):,} tree leaves without data."


def remap_plot_options(options, renames):
    """Rename column references without changing titles or other text settings."""
    from .basic_options import COLUMNS, MULTI_COLUMNS
    from .hierarchy_options import COLUMNS as HIERARCHY_COLUMNS, MULTI_COLUMNS as HIERARCHY_MULTI
    from .scatter_options import COLUMN_OPTIONS
    scalar = COLUMNS | HIERARCHY_COLUMNS | COLUMN_OPTIONS
    multi = MULTI_COLUMNS | HIERARCHY_MULTI
    updated = deepcopy(options or {})
    for key, value in updated.items():
        if key in scalar and isinstance(value, str):
            updated[key] = renames.get(value, value)
        elif key in multi and isinstance(value, list):
            updated[key] = [renames.get(v, v) for v in value]
        elif key in {"labels", "category_orders", "hover_data_format"} and value:
            try:
                mapping = json.loads(value) if isinstance(value, str) else value
                if isinstance(mapping, dict):
                    renamed = {renames.get(k, k): v for k, v in mapping.items()}
                    updated[key] = json.dumps(renamed) if isinstance(value, str) else renamed
            except (ValueError, TypeError):
                pass  # Keep invalid drafts available for the existing validators.
    return updated
