import dash
from dash import dcc
from dash import Input, Output, callback
from dash import html
import datetime
import pandas as pd

import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

import os

HERE = os.path.dirname(__file__)
DATA_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "gen_data.xlsx"))
NEW_DATA_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "stats.xlsx"))

new_df = pd.read_excel(DATA_FILE)
df = pd.read_excel(NEW_DATA_FILE)


def get_status_z():

    fig = px.histogram(data_frame=df, x='status_z', color='status_z')
    fig.update_layout(legend_title_text='Статус заявления')

    fig.update_layout(
        yaxis_title="Количество",
        xaxis_title="Тип статуса"
    )

    return fig


def get_status_p():
    tmp_df = pd.value_counts(new_df['status_p'])

    fig = px.pie(data_frame=tmp_df, values='status_p', names=tmp_df.index,
                 title='Статус заявления')

    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=20),
    )

    return fig

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
                options=['Все', 'Лично', 'По почте', 'В личном кабинете'],
                value='Все',
                searchable=False,
                clearable=False
            )
        ]),
    ]),
    dbc.Row(children=[ # Строчка с самим графиком
        dcc.Graph(id='daily_load_plot')
    ])
])

status_z = dbc.Col(children=[ # График статус заявления
    dcc.Graph(figure=get_status_z(), id='status_z_plot')
])

status_pz = html.Div(children=[ # Блок с графиком статуса заявления
    html.H2('Статус заявлений'),
    dbc.Row(children=[status_z])
])

layout = html.Div(children=[
    html.H2('Распределение нагрузки по дням'),
    daily_load,
    status_pz
])

@callback(
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

    if type != 'Все':
        tmp_df = new_df.loc[(new_df['date'] >= start) & (new_df['date'] <= end) & (new_df['type_p'] == pattetn[type])].groupby(['date'])
    else:
        tmp_df = new_df.loc[(new_df['date'] >= start) & (new_df['date'] <= end)].groupby(['date'])


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