"""Dash wiring for the active dataset; all mutations use one store writer."""
import json
from dash import Input, Output, State, ctx, dcc, no_update
from .data_manager import (apply_columns, apply_metadata, association, dashboard_records,
                           dataset_frame, parse_upload, preview, remap_plot_options)


def register_data_callbacks(app, tree):
    leaves = [leaf.name for leaf in tree.leaves()] if tree is not None else []

    @app.callback(
        Output("data-manager-workspace", "style"), Output("plots-layout", "style"),
        Input("open-data-manager", "n_clicks", allow_optional=True), Input("close-data-manager", "n_clicks"),
        prevent_initial_call=True,
    )
    def activate_data_manager(open_clicks, close_clicks):
        if ctx.triggered_id == "open-data-manager" and not open_clicks:
            return no_update, no_update
        opened = ctx.triggered_id == "open-data-manager"
        return ({}, {"display": "none"}) if opened else ({"display": "none"}, {})

    @app.callback(
        *[Output(f"data-manager-{tab}", "style") for tab in ("overview", "preview", "metadata", "columns")],
        Input("data-manager-tab", "value"),
    )
    def switch_data_tab(active):
        return tuple({} if tab == active else {"display": "none"} for tab in ("overview", "preview", "metadata", "columns"))

    @app.callback(
        Output("dataset-store", "data"), Output("data-manager-status", "children"),
        Input("upload-data", "contents", allow_optional=True), Input("rename-dataset", "n_clicks"),
        Input("delete-dataset", "submit_n_clicks"), Input("save-data-metadata", "n_clicks"),
        Input("apply-data-columns", "n_clicks"),
        State("upload-data", "filename", allow_optional=True), State("dataset-store", "data"), State("dataset-name-input", "value"),
        State("data-metadata-editor", "data"), State("data-columns-editor", "data"),
        State("data-primary-key", "value"), State("data-tree-key", "value"), prevent_initial_call=True,
    )
    def edit_dataset(contents, rename, delete, metadata, columns, filename, dataset, name, metadata_rows, column_rows, primary, key):
        trigger = ctx.triggered_id
        try:
            if trigger == "upload-data":
                if not contents:
                    return (no_update,) * 2
                updated = parse_upload(contents, filename)
                message = f"Loaded {filename}: {len(updated['records']):,} rows × {len(updated['columns'])} columns."
                return updated, message
            if not dataset:
                raise ValueError("Upload a dataset first.")
            if trigger == "delete-dataset":
                return None, "Dataset deleted."
            if trigger == "rename-dataset":
                if not name or not name.strip():
                    raise ValueError("Enter a dataset name.")
                updated = {**dataset, "name": name.strip()}
            elif trigger == "save-data-metadata":
                updated = apply_metadata(dataset, metadata_rows)
            elif trigger == "apply-data-columns":
                updated = apply_columns(dataset, column_rows, primary, key)
            else:
                return (no_update,) * 2
            return updated, "Changes saved."
        except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
            message = f"Could not apply changes: {exc}"
            return no_update, message

    @app.callback(Output("upload-data-status", "children"), Input("dataset-store", "data"),
                  Input("data-manager-status", "children"))
    def upload_status(dataset, message):
        return message or (f"Active dataset: {dataset['name']}" if dataset else "No dataset loaded.")

    @app.callback(
        Output("data-manager-empty", "style"), Output("data-manager-name", "children"),
        Output("data-manager-summary", "children"), Output("data-manager-association", "children"),
        Output("dataset-name-input", "value"), Output("data-metadata-editor", "data"),
        Output("data-columns-editor", "data"), Output("data-primary-key", "options"),
        Output("data-primary-key", "value"), Output("data-tree-key", "options"), Output("data-tree-key", "value"),
        Output("data-preview-table", "columns"), Output("data-preview-visible", "options"),
        Output("data-preview-visible", "value"),
        Input("dataset-store", "data"),
    )
    def describe_dataset(dataset):
        if not dataset:
            return {}, "No dataset", "", association(None, leaves), "", [], [], [], None, [], None, [], [], []
        frame = dataset_frame(dataset)
        columns = dataset["columns"]
        metadata = [{**c, "missing": int(frame[c['name']].isna().sum()),
                     "unique": int(frame[c['name']].nunique())} for c in columns]
        choices = [{"label": c["name"], "value": c["id"]} for c in columns]
        table_cols = [{"name": c["name"], "id": c["name"]} for c in columns]
        summary = f"{len(frame):,} rows · {len(columns)} columns · {int(frame.isna().sum().sum()):,} missing values"
        return ({"display": "none"}, dataset["name"], summary, association(dataset, leaves), dataset["name"],
                metadata, columns, choices, dataset["primary_key"], choices, dataset["tree_key"], table_cols,
                [{"label": c["name"], "value": c["name"]} for c in columns],
                [c["name"] for c in columns if c["visible"]])

    @app.callback(
        Output("data-preview-table", "data"), Output("data-preview-table", "page_count"), Output("data-preview-count", "children"),
        Input("dataset-store", "data"), Input("data-preview-table", "page_current"),
        Input("data-preview-table", "sort_by"), Input("data-preview-search", "value"),
    )
    def preview_dataset(dataset, page, sort, search):
        # Discard sort keys removed by a schema edit.
        names = {c["name"] for c in (dataset or {}).get("columns", [])}
        sort = [s for s in (sort or []) if s["column_id"] in names]
        rows, pages, total = preview(dataset, page, search=search, sort=sort)
        return rows, pages, f"{total:,} matching rows · 50 rows per page"

    @app.callback(Output("data-preview-table", "hidden_columns"),
                  Input("data-preview-visible", "value"), State("data-preview-table", "columns"))
    def visible_columns(visible, columns):
        return [c["id"] for c in (columns or []) if c["id"] not in (visible or [])]

    @app.callback(Output("data-preview-table", "page_current"),
                  Input("dataset-store", "data"), Input("data-preview-search", "value"), Input("data-preview-table", "sort_by"),
                  prevent_initial_call=True)
    def reset_preview_page(*_):
        return 0

    @app.callback(Output("data-metadata-download", "data"), Input("export-data-metadata", "n_clicks"),
                  State("dataset-store", "data"), prevent_initial_call=True)
    def export_metadata(clicks, dataset):
        if not dataset:
            return no_update
        return dcc.send_string(json.dumps({k: v for k, v in dataset.items() if k != "records"}, indent=2), "metadata.json")

    @app.callback(
        Output("species-table", "data"), Output("species-table", "columns"),
        Output("species-table", "selected_rows", allow_duplicate=True),
        Output("selected-species", "data", allow_duplicate=True),
        Output("plot-instances", "data", allow_duplicate=True),
        Output("dataset-schema", "data"),
        Output("scatter-options-store", "data", allow_duplicate=True),
        Output("pie-options-store", "data", allow_duplicate=True),
        Output("basic-options-store", "data", allow_duplicate=True),
        Output("hierarchy-options-store", "data", allow_duplicate=True),
        Input("dataset-store", "data"), State("species-table", "data"), State("selected-species", "data"),
        State("dataset-schema", "data"), State("plot-instances", "data"),
        State("scatter-options-store", "data"), State("pie-options-store", "data"),
        State("basic-options-store", "data"), State("hierarchy-options-store", "data"),
        prevent_initial_call=True,
    )
    def synchronize_dataset(dataset, current_rows, selected, previous_schema=None, instances=None,
                            scatter=None, pie=None, basics=None, hierarchies=None):
        rows, columns = dashboard_records(dataset)
        schema = (dataset or {}).get("columns", [])
        old_names = {c["id"]: c["name"] for c in (previous_schema or [])}
        renames = {old_names[c["id"]]: c["name"] for c in schema
                   if c["id"] in old_names and old_names[c["id"]] != c["name"]}
        plots = no_update
        stores = (no_update,) * 4
        if renames:
            plots = [{**p, "options": remap_plot_options(p.get("options"), renames)} for p in (instances or [])]
            stores = (remap_plot_options(scatter, renames), remap_plot_options(pie, renames),
                      {k: remap_plot_options(v, renames) for k, v in (basics or {}).items()},
                      {k: remap_plot_options(v, renames) for k, v in (hierarchies or {}).items()})
        if not dataset:
            plots = [{"id": "plot_1", "type": None, "options": {}, "visible": True, "pinned": False}]
            stores = ({}, {}, {}, {})
        if rows == (current_rows or []):
            return no_update, columns, no_update, no_update, plots, schema, *stores
        return rows, columns, [], [], plots, schema, *stores
