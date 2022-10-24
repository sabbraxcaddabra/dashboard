# ! /home/sabbraxcaddabra/dash_app_env/bin/python3
import dash
import dash_auth
from dash import dcc
from dash import Input, Output, callback
from dash import html
import datetime
import json
import os

HERE = os.path.dirname(__file__)
CONFIG_FILE = os.path.abspath(os.path.join(HERE, ".", "config.json"))

with open(CONFIG_FILE, encoding='utf-8') as config_file:
    config = json.load(config_file)
    users = config['users']

import dash_bootstrap_components as dbc

from pages import daily_load_page, stats_page, last_year_compare_page, occupancy_page, fst_w_page, enrolled_page, map_page

external_stylesheets = [dbc.themes.GRID,
                      dbc.themes.BOOTSTRAP,
                      'https://codepen.io/chriddyp/pen/bWLwgP.css'
                      ]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True,
                meta_tags=[
                    {'name': 'viewport', 'content': 'width=device-width, initial-scale=0.7'}
                ]
                )

auth = dash_auth.BasicAuth(
    app,
    users
)

server = app.server

app.title = 'Статистика ОИАС'

page_header = dbc.Row(children=[ # Заголовочная строка с заголовком и текущем временем
        dbc.Col(
            html.Img(src='https://priem.voenmeh.ru/d/sayt_logo.png'), width=2
        ),
        dbc.Col(html.Div("Статистика приема БГТУ \"ВОЕНМЕХ\" им. Д.Ф. Устинова",
                         style={'textAlign': 'left', 'fontSize': '24px'}), width=7),
        dbc.Col([
            html.Div(children=f"Дата и время: {datetime.datetime.now().strftime('%d-%m-%y  %H:%M:%S')}",
                     id='datetime-header', style={'textAlign': 'center', 'fontSize': '18px'}),
            dcc.Interval(id='minut-interval')
        ], align='center')
    ])

report_type = html.Div(children=[
    html.H2('Тип отчета'),
    dcc.Dropdown(
        id='report_type',
        options=['Аналитика по зачисленным',
                 'Карта',
                 'Анализ первой волны',
                 'Заполняемость',
                 'Деканское',
                 'Ежедневный отчет',
                 'Сравнение с ПК 2021'], value='Аналитика по зачисленным', clearable=False
    ),
    html.Br(),
])

app.layout = dbc.Container(children=[
    page_header,
    report_type,
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
], fluid='sm')#style={'marginLeft': 250, 'marginRight': 250})

@app.callback(
    Output('url', 'pathname'),
    [Input('report_type', 'value')]
)
def refresh_page(report_type):

    report_dict = {
        'Карта': '/map',
        'Аналитика по зачисленным': '/enrolled_page',
        'Ежедневный отчет': '/daily_load_page',
        'Деканское': '/stats_page',
        'Сравнение с ПК 2021': '/compare_2021_page',
        'Заполняемость': '/occupancy_page',
        'Анализ первой волны': '/fst_w_page'
    }
    return report_dict[report_type]

@app.callback(
    Output('datetime-header', 'children'),
    [Input('minut-interval', 'n_intervals')]
)
def update_datetime(n):
    '''
    Фунция обновляет текущее время на странице
    :param n: по большому счету не нужен, нужен только для того чтобы функция заработало
    :return: Div с текущим временем
    '''
    date = datetime.datetime.now()
    return html.Div(children=f"Дата и время: {date.strftime('%d-%m-%y  %H:%M:%S')}")

@callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/daily_load_page':
        return daily_load_page.layout
    elif pathname == '/stats_page':
        return stats_page.layout
    elif pathname == '/compare_2021_page':
        return last_year_compare_page.layout
    elif pathname == '/occupancy_page':
        return occupancy_page.layout
    elif pathname == '/fst_w_page':
        return fst_w_page.layout
    elif pathname == '/enrolled_page':
        return enrolled_page.layout
    elif pathname == '/map':
        return map_page.layout
    else:
        return '404'

if __name__ == '__main__':
    app.run('172.24.135.27', port=5000, debug=True)

    # app.run(debug=True)