import dash
from dash import dcc
from dash import Input, Output, callback
from dash import html
import datetime
import pandas as pd

import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

from getpass import getpass
from sqlalchemy import create_engine
import pymysql
import datetime

import os

from . import data_loader

DATA_LOADER = data_loader.DailyDataLoader()


HERE = os.path.dirname(__file__)
DATA_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "gen_data.xlsx"))
NEW_DATA_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "stats.xlsx"))

new_df = pd.read_excel(DATA_FILE)
df = pd.read_excel(NEW_DATA_FILE)

real_df = DATA_LOADER.load_data()

def count_orig(series):
    counts = pd.value_counts(series).get(1, 0)
    return counts

def get_today_table():
    today = datetime.date.today()

    today_df = real_df[real_df['add_data'] == today]

    grouped = today_df.groupby(['spec_code', 'spec_name', 'edu_form']).agg({'spec_name': 'count', 'original': count_orig})

    grouped = grouped.rename(columns={'spec_name': 'Заявлений', 'original': 'Оригиналов'})

    df_table = grouped.reset_index()
    df_table.loc[df_table['spec_code'].duplicated(), 'spec_code'] = ''
    df_table.loc[df_table['spec_name'].duplicated(), 'spec_name'] = ''

    df_table = df_table.rename(columns={
        'spec_code': 'Код',
        'spec_name': 'Название',
        'edu_form': 'Форма обучения'
        }
    )

    table = go.Table(
        header=dict(values=df_table.columns.tolist()),
        cells=dict(values=df_table.T.values)
    )


    fig = go.Figure(data=table).update_layout()

    height = df_table.shape[0] * 50
    if height < 200:
        height = 200

    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=10, b=0),
    )

    return fig

def get_type_dropdown_options():
    options = list(real_df['post_method'].unique())
    return ['Все'] + options

def get_min_data():
    min_data = real_df['add_data'].min()
    min_data = datetime.datetime.strptime(min_data, 'yyyy-mm-dd')
    return min_data

def get_max_data():
    min_data = real_df['add_data'].max()
    min_data = datetime.datetime.strptime(min_data, 'yyyy-mm-dd')
    return min_data

def get_status_z():  # Отрисовывает график со статусами заявлений

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
    html.Div('Сводка на сегодня'),
    dcc.Graph(figure=get_today_table(), id='today_table'),
    dbc.Row(children=[  # Строчка с распределением нагрузки по дням и типу подачи заявления
        dbc.Col([
            html.Div('Период дней'),
            dcc.DatePickerRange(  # Выбор промежутка дат
                id='pick_a_date',
                start_date=real_df['add_data'].min(),
                end_date=real_df['add_data'].max(),
                max_date_allowed=real_df['add_data'].max(),
                min_date_allowed=real_df['add_data'].min()
            )
        ]),
        dbc.Col(children=[
            html.Div('Тип заявления'),
            dcc.Dropdown(
                id='type_z_dropdown',
                options=['Все', 'Заявление с согласием', 'Заявление с оригиналом'],
                value='Все',
                searchable=False,
                clearable=False
            )
        ]),
        dbc.Col(children=[
            html.Div('Тип подачи заявления'),
            dcc.Dropdown(
                id='type_dropdown',
                options=get_type_dropdown_options(),
                value='Все',
                searchable=False,
                clearable=False
            )
        ]),
    ]),
    dbc.Row(children=[  # Строчка с самим графиком
        dcc.Graph(id='daily_load_plot')
    ])
])

status_z = dbc.Col(children=[  # График статус заявления
    dcc.Graph(figure=get_status_z(), id='status_z_plot')
])

status_pz = html.Div(children=[  # Блок с графиком статуса заявления
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
def plot_daily_load(start, end, post_type):
    '''
    Функция отрисовывает график нагрузки по дням
    :param start: Начало периода
    :param end: Конец периода
    :param type: Тип подачи заявления
    :return: график типа area
    '''

    start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
    end = datetime.datetime.strptime(end, '%Y-%m-%d').date()

    locate_date = {  # Переименование месяца в дате
        '03': 'Март',
        '04': 'Апрель',
        '05': 'Май',
        '07': 'Июль',
        '06': 'Июнь'
    }

    above = real_df['add_data'] >= start
    below = real_df['add_data'] <= end

    tmp_df = real_df.loc[above & below]
    
    if post_type != 'Все':
        tmp_df = tmp_df[tmp_df['post_method'] == post_type]

    counts = pd.value_counts(tmp_df['add_data'])
    counts = counts.sort_index()

    date = counts.index
    values = counts.values

    new_date = []

    for dat in date:
        new_dat = str(dat).split('-')
        new_dat[1] = locate_date[new_dat[1]]
        new_date.append('-'.join(new_dat))

    fig = px.area(x=new_date, y=values)
    fig.update_xaxes(title_text='Дата')
    fig.update_yaxes(title_text='Число заявлений')

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )

    return fig
