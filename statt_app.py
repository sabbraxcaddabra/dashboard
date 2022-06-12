import dash
from dash import dcc
from dash import Input, Output
from dash import html
import datetime
import pandas as pd

import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go


df = pd.read_excel('gen_data.xlsx')


def get_status_z():

    tmp_df = pd.value_counts(df['status_z'])

    fig = px.pie(data_frame=tmp_df, values='status_z', names=tmp_df.index,
                 title='Статус заявления')

    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
    )

    return fig


def get_status_p():
    tmp_df = pd.value_counts(df['status_p'])

    fig = px.pie(data_frame=tmp_df, values='status_p', names=tmp_df.index,
                 title='Статус заявления')

    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=20),
    )

    return fig


def get_spec_frec():

    spec_dict = {
        i:name for i, name in zip(range(0, 15), 'qwertyuiopasdfg'.upper())
    }

    tmp_df = df.groupby(['name']).count()['id']

    fig = go.Figure(data=[
        go.Bar(y=[spec_dict[i] for i in tmp_df.index], x=tmp_df, orientation='h')
    ])

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )

    fig.update_xaxes(title_text='Число заявлений')
    fig.update_yaxes(title_text='Код специальности')
    # fig = px.histogram(x=[spec_dict[i] for i in tmp_df.index], y=tmp_df)
    return fig



external_stylesheets = [dbc.themes.GRID,
                      dbc.themes.BOOTSTRAP,
                      'https://codepen.io/chriddyp/pen/bWLwgP.css'
                      ]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                meta_tags=[
                    {'name': 'viewport', 'content': 'width=device-width, initial-scale=0.7'}
                ]
                )

page_header = dbc.Row(children=[ # Заголовочная строка с заголовком и текущем временем
        dbc.Col(html.Div("Статистика приема БГТУ им. Д.Ф. Устинова \"Военмех\"",
                         style={'textAlign': 'center', 'fontSize': '18px'})),
        dbc.Col([
            html.Div(children=f"Дата и время: {datetime.datetime.now().strftime('%d-%m-%y  %H:%M:%S')}",
                     id='datetime-header', style={'textAlign': 'center', 'fontSize': '18px'}),
            dcc.Interval(id='minut-interval')
        ], align='center')
    ])

daily_load = html.Div(children=[
    dbc.Row(children=[  # Строчка с распределением нагрузки по дням и типу подачи заявления
        dbc.Col([
            html.Div('Период дней'),
            dcc.DatePickerRange(  # Выбор промежутка дат
                id='pick_a_date',
                start_date=datetime.date(year=2022, month=6, day=30),
                end_date=datetime.date(year=2022, month=7, day=30),
                max_date_allowed=datetime.date(year=2022, month=7, day=30),
                min_date_allowed=datetime.date(year=2022, month=6, day=30)
            )
        ]),
        dbc.Col(children=[
            html.Div('Тип подачи заявления'),
            dcc.Dropdown(
                id='type_dropdown',
                options=['Лично', 'По почте', 'В личном кабинете'],
                value='Лично',
                searchable=False
            )
        ]),
    ]),
    dbc.Row(children=[ # Строчка с самим графиком
        dcc.Graph(id='daily_load_plot')
    ])
])

name_frequency = html.Div(children=[ # График с распределением по заявлениям
    dcc.Graph(figure=get_spec_frec(), id='spec_hist')
])

status_z = dbc.Col(children=[ # График статус заявления
    dcc.Graph(figure=get_status_z(), id='status_z_plot')
])
status_p = dbc.Col(children=[ # График статус человека
    dcc.Graph(figure=get_status_p(), id='status_p_plot')
])

status_pz = html.Div(children=[ # Блок с графиками статусов заявления и человека
    html.H2('Статус заявления/ Статус человека'),
    dbc.Row(children=[status_z, status_p])
])

mean_point = html.Div(children=[ # Блок с распределением среднего балла по специальностям и формам обучения
    html.H2('Распределение балла по специальностям и формам обучения'),
    dbc.Row(children=[
        dbc.Col(children=[
            dcc.Dropdown(id='edu_form', options=[
                {'label': 'Очное', 'value': 0},
                {'label': 'Заочное', 'value': 1},
                {'label': 'Очно-заочное', 'value': 2}
            ], value=0)
        ]),
        dbc.Col(children=[
            dcc.Dropdown(id='spec_name', options={
                name:i for i, name in zip('qwertyuiopasdfg'.upper(), range(0, 15))
            }, value=0)
        ])
    ]),
    dcc.Graph(id='mean_point_plot')
])

app.layout = html.Div(children=[
    page_header,
    html.H2('Нагрузка по дням'),
    daily_load,
    html.H2('Заполняемость по специальностям'),
    name_frequency,
    status_pz,
    mean_point
], style={'marginLeft': 250, 'marginRight': 250})


@app.callback(
    Output('mean_point_plot', 'figure'),
    [Input('spec_name', 'value'), Input('edu_form', 'value')]
)
def update_mean_point_plot(spec_name, edu_type):

    if isinstance(spec_name, str):
        spec_name = int(spec_name)

    tmp_df = df.loc[(df['name'] == spec_name) & (df['edutype'] == edu_type)]

    fig = px.histogram(data_frame=tmp_df, x='mean_point')

    return fig

@app.callback(
    Output('daily_load_plot', 'figure'),
    [Input("pick_a_date", "start_date"), Input("pick_a_date", "end_date"), Input('type_dropdown', 'value')]
)
def plot_daily_load(start, end, type):
    '''
    Функция отрисовывает график нагрузки по дням
    :param start: Начало периода
    :param end: Конец периода
    :param type: Тип подачи заявления
    :return: график типа area
    '''
    pattetn = {
        'Лично': 0, 'По почте': 1, 'В личном кабинете': 2
    }

    locate_date = { # Переименование месяца в дате
        '07':'Июль',
        '06': 'Июнь'
    }

    tmp_df = df.loc[(df['date'] >= start) & (df['date'] <= end) & (df['type_p'] == pattetn[type])].groupby(['date'])


    sum_counts = tmp_df.count()['id']

    date = sum_counts.index.date

    new_date = []

    for dat in date:
        new_dat = str(dat).split('-')
        new_dat[1] = locate_date[new_dat[1]]
        new_date.append('-'.join(new_dat))

    fig = px.area(x=new_date, y=sum_counts)
    fig.update_xaxes(title_text='Дата')
    fig.update_yaxes(title_text='Число заявлений')

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )

    return fig


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


if __name__ == "__main__":
    pass
    app.run_server(debug=True)
    # app.run_server('172.24.135.27', debug=True)
    # app.run_server('192.168.0.188', debug=True)