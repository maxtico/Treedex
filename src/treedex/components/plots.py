from dash import dcc, html
import plotly.express as px
import dash_bootstrap_components as dbc
from treedex.treedexcolors import *


theme = 'plotly_white'
storage_type = 'local'
scatter_index = 0
testindex = 0

########################################
#### scatter plot

def make_scatter_plot(
    dfr,
    selection=None,
    x=None,
    y=None,
    color=None,
    symbol=None,
    size=None,
    text=None,
    hover_name="Species",
    hover_data=None,
    facet_row=None,
    facet_col=None,
    facet_col_wrap=0,
    facet_row_spacing=None,
    facet_col_spacing=None,
    error_x=None,
    error_x_minus=None,
    error_y=None,
    error_y_minus=None,
    animation_frame=None,
    animation_group=None,
    opacity=1.0,
    size_max=28,
    color_discrete_palette="Plotly",
    color_continuous_scale="Viridis",
    range_color_min=None,
    range_color_max=None,
    color_continuous_midpoint=None,
    marginal_x=None,
    marginal_y=None,
    render_mode="auto",
    log_x=False,
    log_y=False,
    range_x_min=None,
    range_x_max=None,
    range_y_min=None,
    range_y_max=None,
    orientation=None,
    trendline=None,
    trendline_scope="trace",
    trendline_color_override=None,
    title="Scatter plot",
    subtitle=None,
    template=theme,
):
    discrete_sequences = {
        name: getattr(px.colors.qualitative, name)
        for name in ("Plotly", "D3", "G10", "T10", "Alphabet", "Dark24", "Light24")
    }
    range_color = (
        [range_color_min, range_color_max]
        if range_color_min is not None and range_color_max is not None else None
    )
    range_x = [range_x_min, range_x_max] if range_x_min is not None and range_x_max is not None else None
    range_y = [range_y_min, range_y_max] if range_y_min is not None and range_y_max is not None else None
    figure = px.scatter(
        data_frame=dfr, x=x, y=y, color=color, symbol=symbol, size=size, text=text,
        hover_name=hover_name, hover_data=hover_data or None, custom_data=["Species"],
        facet_row=facet_row, facet_col=facet_col, facet_col_wrap=facet_col_wrap or 0,
        facet_row_spacing=facet_row_spacing, facet_col_spacing=facet_col_spacing,
        error_x=error_x, error_x_minus=error_x_minus, error_y=error_y,
        error_y_minus=error_y_minus, animation_frame=animation_frame,
        animation_group=animation_group, opacity=opacity, size_max=size_max,
        color_discrete_sequence=discrete_sequences.get(color_discrete_palette),
        color_continuous_scale=color_continuous_scale, range_color=range_color,
        color_continuous_midpoint=color_continuous_midpoint, marginal_x=marginal_x,
        marginal_y=marginal_y, render_mode=render_mode, log_x=log_x, log_y=log_y,
        range_x=range_x, range_y=range_y, orientation=orientation,
        trendline=trendline, trendline_scope=trendline_scope,
        trendline_color_override=trendline_color_override, title=title,
        subtitle=subtitle, template=None if template == "none" else template,
    ).update_layout(
        # height=500, width=600,
        clickmode='event+select',
        dragmode='select',
        uirevision=True,
        selectionrevision=False,
    )

    selected_names = {
        str(dfr.iloc[index]["Species"]).casefold()
        for index in (selection or [])
        if 0 <= index < len(dfr)
    }
    for trace in figure.data:
        if trace.type not in ("scatter", "scattergl"):
            continue
        if size is None:
            trace.update(marker_size=14)
        if selected_names:
            trace_customdata = trace.customdata if trace.customdata is not None else []
            trace_selection = [
                index
                for index, customdata in enumerate(trace_customdata)
                if customdata and str(customdata[0]).casefold() in selected_names
            ]
            trace.update(
                selectedpoints=trace_selection,
                unselected_marker={'opacity': 0.4, 'color': '#999999'},
                selected_marker={'opacity': 0.95, 'color': sel_color},
            )

    return figure


scatter_config = {'scrollZoom': False,  # True, False
                  'doubleClick': 'reset',  # 'reset', 'autosize' or 'reset+autosize', False
                  'showTips': False,  # True, False
                  'displayModeBar': 'hover',  # True, False, 'hover'
                  'displaylogo': False,
                  'modeBarButtonsToRemove': ['toImage', 'resetScale', 'lasso']  # , 'zoom', 'pan']
                  }


def make_scatter_menu(
    id_index,
    dataset_options=None,
    dataset_value=None,
    x_options=None,
    x_value=None,
    y_options=None,
    y_value=None,
    title_value=""
): #, colnames, current_options):
    print('** make_scatter_menu')

    return html.Div(
        [
            html.Div("Scatter filters", style={"fontWeight": "bold", "marginBottom": "6px"}),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Title", className="mb-1"),
                            dcc.Input(
                                id={'type': 'scatter_inputtext', 'index': id_index, 'property': 'title'},
                                placeholder='Enter title here',
                                value=title_value,
                                style={"width": "100%"}
                            ),
                        ],
                        md=3
                    ),
                    dbc.Col(
                        [
                            html.Label("Data", className="mb-1"),
                            dcc.Dropdown(
                                id={'type': 'scatter_dropdown', 'index': id_index, 'property': 'dataset'},
                                options=dataset_options or [],
                                value=dataset_value
                            ),
                        ],
                        md=3
                    ),
                    dbc.Col(
                        [
                            html.Label("X axis", className="mb-1"),
                            dcc.Dropdown(
                                id={'type': 'scatter_dropdown', 'index': id_index, 'property': 'x'},
                                options=x_options or [],
                                value=x_value
                            ),
                        ],
                        md=3
                    ),
                    dbc.Col(
                        [
                            html.Label("Y axis", className="mb-1"),
                            dcc.Dropdown(
                                id={'type': 'scatter_dropdown', 'index': id_index, 'property': 'y'},
                                options=y_options or [],
                                value=y_value
                            ),
                        ],
                        md=3
                    ),
                ],
                class_name="g-2"
            ),
        ],
        id={'type': 'scatter_menu', 'index': id_index},
        style={
            "marginBottom": "12px",
            "padding": "10px",
            "border": "1px solid #d7e3f5",
            "borderRadius": "10px",
            "backgroundColor": "#f8fbff"
        }
    )



### always make default options here
def make_scatter_combo(dataset='<empty>', dfr=[]):  ## need to deal with this special value
    global scatter_index
    scatter_index += 1

    if dfr:
        first_numeric_cols=[k for k, v in dfr[0].items() if type(v) in (int, float)][:2]
        if not first_numeric_cols:
            first_numeric_cols=[None]
        scatter_options={'title': '',
                         'x':first_numeric_cols[0] ,
                         'y':first_numeric_cols[-1],
                         'dataset': dataset}
    else:
        raise Exception('Will handle this eventually, but now you must call make_scatter_combo with an init dataset name and dfr')
        scatter_options={}
    print(('** making scatter combo', scatter_index, dataset, scatter_options) )

    out = dbc.Row(
        dbc.Col([
            dbc.Row(dbc.Col(
                dbc.Button("Scatter", size="sm", n_clicks=0,
                           id={'type': 'scatter_configure',  'index': scatter_index}),
                class_name="g-0")),

            #html.Div(id={'type': 'scatter_menucontainer', 'dataset':'', 'index': scatter_index}),
            dbc.Row(dbc.Col(
                make_scatter_menu(scatter_index)

            )),

            dbc.Row(dbc.Col(
                [dcc.Graph(id={'type': 'scatter_graph', 'dataset':dataset, 'index': scatter_index},
                           config=scatter_config),
                 dcc.Store(id={'type': 'scatter_store', 'dataset':dataset, 'index':scatter_index},
                           storage_type=storage_type
                           #data=scatter_options #ignored by dash!!
                           )]

                 ### data init value is ignored or what??
            ))],
            class_name="border border-primary g-0"
        )
    )

    return out
