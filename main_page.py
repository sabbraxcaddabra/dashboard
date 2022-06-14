import dash
from dash import dcc
from dash import Input, Output, callback
from dash import html
import datetime

import dash_bootstrap_components as dbc

from pages import daily_load_page, stats_page

external_stylesheets = [dbc.themes.GRID,
                      dbc.themes.BOOTSTRAP,
                      'https://codepen.io/chriddyp/pen/bWLwgP.css'
                      ]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True,
                meta_tags=[
                    {'name': 'viewport', 'content': 'width=device-width, initial-scale=0.7'}
                ]
                )

server = app.server

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
        options=['Деканское', 'Ежедневный отчет'], value='Деканское'
    )
])

app.layout = html.Div(children=[
    page_header,
    report_type,
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
], style={'marginLeft': 250, 'marginRight': 250})

@app.callback(
    Output('url', 'pathname'),
    [Input('report_type', 'value')]
)
def refresh_page(report_type):

    report_dict = {
        'Ежедневный отчет': '/daily_load_page',
        'Деканское': '/stats_page'
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
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(debug=True)

    # app.run_server(debug=True)