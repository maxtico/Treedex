"""Persistent workspace for inspecting and documenting the active dataset."""
from dash import dash_table, dcc, html
from ..data_manager import TYPES, ROLES


def editor(component_id, columns, dropdown=None):
    return dash_table.DataTable(
        id=component_id, columns=columns, data=[], editable=True,
        hidden_columns=["id"], dropdown=dropdown or {},
        page_size=20, style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "minWidth": "120px", "maxWidth": "300px",
                    "whiteSpace": "normal", "padding": "10px"},
        style_header={"fontWeight": "600"},
    )


def data_manager_layout():
    def column(name, label, editable=True, presentation="input", **kwargs):
        return {"id": name, "name": label, "editable": editable, "presentation": presentation, **kwargs}

    return html.Section([
        html.Div([html.H2("Data Manager"), html.Button("Back to plots", id="close-data-manager")],
                 className="data-manager-heading"),
        html.P("Inspect and document the active dataset. Uploading a file replaces it."),
        html.Div(id="data-manager-empty", children="No dataset loaded. Use Data → Upload data to get started."),
        html.Div(id="data-manager-status", role="status"),
        dcc.Tabs(id="data-manager-tab", value="overview", children=[
            dcc.Tab(label=label, value=value) for value, label in
            (("overview", "Overview"), ("preview", "Data Preview"), ("metadata", "Metadata"), ("columns", "Columns"))
        ]),
        html.Div([
            html.H3(id="data-manager-name"), html.Div(id="data-manager-summary", className="data-manager-summary"),
            html.P(id="data-manager-association"),
            html.Label("Dataset name", htmlFor="dataset-name-input"),
            dcc.Input(id="dataset-name-input", type="text", maxLength=200),
            html.Button("Rename dataset", id="rename-dataset"),
            dcc.ConfirmDialogProvider(html.Button("Delete dataset", className="data-manager-danger"),
                id="delete-dataset", message="Delete the active dataset and its metadata? This clears linked plots and selections."),
        ], id="data-manager-overview", className="data-manager-tab"),
        html.Div([
            html.Label("Search all columns (literal text)", htmlFor="data-preview-search"),
            dcc.Input(id="data-preview-search", type="search", debounce=True, placeholder="Filter rows…"),
            html.Label("Visible preview columns", htmlFor="data-preview-visible"),
            dcc.Dropdown(id="data-preview-visible", multi=True),
            html.P(id="data-preview-count"),
            dash_table.DataTable(id="data-preview-table", data=[], columns=[], page_current=0,
                page_size=50, page_action="custom", page_count=1, sort_action="custom", sort_mode="multi", sort_by=[],
                style_table={"overflowX": "auto"}, style_cell={"textAlign": "left", "padding": "8px", "maxWidth": "260px",
                    "overflow": "hidden", "textOverflow": "ellipsis"}),
        ], id="data-manager-preview", className="data-manager-tab", style={"display": "none"}),
        html.Div([
            html.P('Describe variables and encode value definitions as JSON, e.g. {"0": "Absent", "1": "Present"}.'),
            editor("data-metadata-editor", [
                column("id", "ID", False), column("name", "Column", False), column("dtype", "Inferred / declared type", False),
                column("missing", "Missing", False, type="numeric"), column("unique", "Distinct", False, type="numeric"),
                column("description", "Description"), column("role", "Role", presentation="dropdown"),
                column("units", "Units"), column("values", "Value definitions (JSON)"),
            ], {"role": {"options": [{"label": r, "value": r} for r in ROLES]}}),
            html.Button("Save metadata", id="save-data-metadata"),
            html.Button("Export saved metadata", id="export-data-metadata"), dcc.Download(id="data-metadata-download"),
        ], id="data-manager-metadata", className="data-manager-tab", style={"display": "none"}),
        html.Div([
            html.P("Edit names, types and positions, then apply together. Invalid conversions leave the dataset unchanged. Visibility controls the preview."),
            html.P("The configured tree key is exposed as Species in plots and the linked species table."),
            editor("data-columns-editor", [column("id", "ID", False), column("name", "Name"),
                column("dtype", "Type", presentation="dropdown"), column("position", "Position", type="numeric"),
                column("visible", "Visible", presentation="dropdown")], {
                    "dtype": {"options": [{"label": t, "value": t} for t in TYPES]},
                    "visible": {"options": [{"label": "Yes", "value": True}, {"label": "No", "value": False}]},
                }),
            html.Label("Primary identifier (unique, nonmissing)", htmlFor="data-primary-key"),
            dcc.Dropdown(id="data-primary-key", placeholder="None"),
            html.Label("Tree key (matches tree leaf names)", htmlFor="data-tree-key"),
            dcc.Dropdown(id="data-tree-key", placeholder="None"),
            html.Button("Apply column changes", id="apply-data-columns"),
        ], id="data-manager-columns", className="data-manager-tab", style={"display": "none"}),
    ], id="data-manager-workspace", className="data-manager", style={"display": "none"})
