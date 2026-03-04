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

def make_scatter_plot(dfr, x, y, title, selection=[]):
    # global testindex
    # testindex+=1
    return px.scatter(data_frame=dfr,
                      x=x,
                      y=y,
                      title=title,
                      template=theme,
                      hover_name="Species").update_layout(
        # height=500, width=600,
        clickmode='event+select',
        dragmode='select',
        uirevision=True,
        selectionrevision=False,
    ).update_traces(selectedpoints=selection,
                    marker_size=14,
                    unselected_marker={'opacity': 0.4,
                                       'color': '#999999'},
                    selected_marker={'opacity': 0.95,
                                     'color': sel_color})


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
