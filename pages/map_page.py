from urllib.request import urlopen
import json

import pandas as pd
import plotly.express as px
import numpy as np

import dash
from dash import dcc
from dash import html
from dash import Input, Output, callback, State, dash_table
import dash_bootstrap_components as dbc
import os

HERE = os.path.dirname(__file__)

MAPPER_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "app1.json"))
LOCALIZATION_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "base_to_rus.json"))
ZAVOD_FILE = os.path.abspath(os.path.abspath(os.path.join(HERE, "..", "data", "zavod.csv")))
PROF_FILE = os.path.abspath(os.path.abspath(os.path.join(HERE, "..", "data", "prof.csv")))
REGIONS_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "regions.csv"))

with urlopen('https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/russia.geojson') as response:
    counties = json.load(response)

with open(MAPPER_FILE, encoding='utf8') as mapper:
    mapper_dict = json.load(mapper)

with open(LOCALIZATION_FILE, encoding='utf8') as localization:
    localization_dict = json.load(localization)

for tmp_id, tmp_dict in enumerate(counties['features']):
    tmp_dict['id'] = tmp_id

def localization(dict_to_localizate):
    tmp_dict = {}
    for key in dict_to_localizate.keys():
        locate_key = localization_dict.get(key)
        if locate_key:
            tmp_dict[locate_key] = dict_to_localizate[key]

    return tmp_dict

map_regio_names = [tmp_dict['properties']['name'] for tmp_dict in counties['features']]
map_regio_id = {tmp_dict['properties']['name']: tmp_dict['id'] for tmp_dict in counties['features']}

df = pd.read_csv(REGIONS_FILE)
zavod_df = pd.read_csv(ZAVOD_FILE)
prof_df = pd.read_csv(PROF_FILE)

df['map_name'] = df['region'].apply(lambda name: mapper_dict.get(name))
df['map_id'] = df['map_name'].apply(lambda map_name: map_regio_id[map_name])

fig = px.choropleth_mapbox(df, geojson=counties, color="count_text", locations="map_id",
                           featureidkey="id", hover_data=['map_name', 'count_apps_enr'],
                           labels={'map_name':'Регион', 'count_apps_enr': 'Кол-во зачисленных', 'count_text': localization_dict['count_text']},
                           color_discrete_map={
                               "менее 10": "darkgreen",
                               "от 20 до 30": "green",
                               "от 30 до 40": "greenyellow",
                               "от 40 до 50": "yellow",
                               "более 200": "darkred",
                               "более 1000": "red"
                           },
                           mapbox_style="carto-positron", zoom=3,
                           center={'lat':55.75, 'lon': 37.61}
                           )

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

layout = html.Div(children=[dcc.Graph(figure=fig, id='graph'),
                            dbc.Modal(children=[
                                dbc.ModalHeader(dbc.ModalTitle(id='regio_modal_title')),
                                dbc.ModalBody(id='regio_modal_body'),
                            ], id='regio_modal', is_open=False, size='xl'),
                            html.Div(id='where')])

@callback(
    [Output("regio_modal", "is_open"), Output("regio_modal_title", 'children'), Output('regio_modal_body', 'children')],
    [Input("graph", "clickData")],
    [State('regio_modal', 'is_open')]
)
def click(clickData, is_open):
    # if not is_open:
    #     is_open = True
    if not clickData:
        raise dash.exceptions.PreventUpdate
    region = clickData['points'][0]['customdata'][0]
    tmp_df = df[df['map_name'] == region]

    regio_dict = tmp_df.to_dict('records')[0]
    regio_dict = localization(regio_dict)
    tmp_df = pd.DataFrame(data={
        'Показатель': list(regio_dict.keys()),
        'Значение': list(regio_dict.values())
    })

    zavod_tmp_df = zavod_df[zavod_df['Регион'] == region]
    prof_tmp_df = prof_df[prof_df['region'] == region]


    zavod_tmp_df = zavod_tmp_df.loc[:, ['Предприятие', 'Кол-во зачисленных']]
    prof_tmp_df = prof_tmp_df.drop('region', axis=1).rename(
        columns=dict(took_part='Количество абитуриентов, прошедших профориентацию',
                     enrolled='Количество зачисленных абитуриентов, прошедших профориентацию',
                     cooperated='Количество школ, с которыми сотрудничает БГТУ "ВОЕНМЕХ"'
                     )
    )

    zavod_table = dash_table.DataTable(
        data=zavod_tmp_df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in zavod_tmp_df.columns],
        style_cell={'textAlign': 'center'},
    )

    if prof_tmp_df.empty:
        prof_table = html.H5('Информации по школам в этом регионе нет')
    else:
        prof_tmp_df = prof_tmp_df.T.reset_index()
        print(prof_tmp_df.empty)
        prof_tmp_df = prof_tmp_df.rename(
            columns={prof_tmp_df.columns[0]: "Показатель", prof_tmp_df.columns[1]: "Значение"})
        prof_table = dash_table.DataTable(
            data=prof_tmp_df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in prof_tmp_df.columns],
            style_cell={'textAlign': 'left'},
        )

    table = dash_table.DataTable(
        data=tmp_df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in tmp_df.columns],
        style_cell={'textAlign': 'left'},
    )

    return not is_open, f'Статистика по региону: {region}', html.Div(children=[
        html.H3('Общая информация'),
        table,
        html.Br(),
        html.H3('Предприятия'),
        zavod_table,
        html.Br(),
        html.H3('Школы'),
        prof_table
    ])