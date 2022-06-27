import dash
from dash import dcc
from dash import Input, Output, callback
from dash import html
import datetime
import pandas as pd
import time

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

def get_budget(series):
    tmp_series = series[series != 'С оплатой обучения']
    return tmp_series.shape[0]

def get_contract(series):
    tmp_series = series[series == 'С оплатой обучения']
    return tmp_series.shape[0]

def count_orig(series):
    counts = pd.value_counts(series).get(1, 0)
    return counts

def day_stats(df):
    grouped = df.groupby(['spec_code', 'spec_name', 'edu_form']).agg(
    spec_name_count=('spec_name', 'count'),
    original_count=('original', count_orig),
    budget=('fintype', get_budget),
    kontract=('fintype', get_contract)
    )
    return grouped.reset_index()

def get_edu_level_by_code(code):
    edu_level_code = int(code.split('.')[1])
    edu_level_codes = {
        3: 0,
        5: 1,
        4: 2
    }
    return edu_level_codes[edu_level_code]

def sort_by_edu_level(grouped):
    grouped['edu_level_code_num'] = grouped['spec_code'].apply(get_edu_level_by_code)
    sorted_df = grouped.sort_values(by='edu_level_code_num', ascending=True)
    del sorted_df['edu_level_code_num']
    return sorted_df

def get_stats(df):
    grouped = day_stats(df)
    df_table = sort_by_edu_level(grouped)
    df_table = df_table.rename(columns={
        'spec_code': 'Код',
        'spec_name': 'Название',
        'edu_form': 'Форма обучения',
        'budget': 'Заявлений на бюджет',
        'kontract': 'Заявлений на контракт',
        'spec_name_count': 'Заявлений всего',
        'original_count': 'Оригиналов',
        }
    )
    return df_table


def get_today_table():
    today = datetime.date.today()
    df = DATA_LOADER.data
    today_df = df[df['add_data'] == today]

    # # grouped = today_df.groupby(['spec_code', 'spec_name', 'edu_form']).agg({'spec_name': 'count', 'original': count_orig})
    # #
    # # grouped = grouped.rename(columns={'spec_name': 'Заявлений', 'original': 'Оригиналов'})
    # #
    # # df_table = grouped.reset_index()
    # # df_table.loc[df_table['spec_code'].duplicated(), 'spec_code'] = ''
    # # df_table.loc[df_table['spec_name'].duplicated(), 'spec_name'] = ''
    # #
    # df_table = df_table.rename(columns={
    #     'spec_code': 'Код',
    #     'spec_name': 'Название',
    #     'edu_form': 'Форма обучения',
    #     'budget': 'Заявлений на бюджет',
    #     'kontract': 'Заявлений на контракт',
    #     'spec_name_count': 'Заявлений всего',
    #     'original_count': 'Оригиналов',
    #     }
    # )


    df_table = get_stats(today_df)
    d_table  = dash.dash_table.DataTable(
        df_table.to_dict('records'),
        [{"name": i, "id": i} for i in df_table.columns],
        style_cell={'textAlign': 'left'},
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

    return d_table

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

    df = DATA_LOADER.data
    df = df.drop_duplicates(subset=['abiturient_id'])

    fig = px.histogram(data_frame=df, x='status_name', color='status_name')
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
    dcc.Download(id='today_report'),
    dcc.Download(id='total_report'),
    dbc.Row(children=[
       dbc.Col(children=[
           html.Div('Дата и время выгрузки'),
       ]),
        dbc.Col(children=[
            html.Div(id='load_date'),
            dcc.Interval(id='load_date_interval', interval=300e3)
        ])
    ]),
    html.Div('Сводка на сегодня'),
    html.Div(id='daily_table'),
    dbc.Row(children=[
        dbc.Col(children=[
            html.Button(id='today_report_button', children='Сформировать отчет за сегодня в Excel')
        ], width=4),
        dbc.Col(children=[
            html.Button(id='total_report_button', children='Сформировать отчет за все время в Excel'),
        ], width=4),
    ]),
    # dcc.Graph(figure=get_today_table(), id='today_table'),
    dbc.Row(children=[  # Строчка с распределением нагрузки по дням и типу подачи заявления
        dbc.Col([
            html.Div('Период дней'),
            dcc.DatePickerRange(  # Выбор промежутка дат
                id='pick_a_date',
                start_date=real_df['add_data'].min(),
                end_date=real_df['add_data'].max(),
                max_date_allowed=real_df['add_data'].max(),
                min_date_allowed=real_df['add_data'].min(),
                display_format='Y-MM-DD'
            )
        ]),
        dbc.Col(children=[
            html.Div('Тип финансирования'),
            dcc.Dropdown(
                id='type_f_dropdown',
                options=['Все', 'Бюджет', 'Контракт'],
                value='Все',
                searchable=False,
                clearable=False
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
    ]),
    dbc.Row(children=[  # Строчка с кумулятивной диаграммой
        dcc.Graph(id='daily_load_cum_plot')
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

def get_df_by_fintype(tmp_df, fintype):
    # Фильтруем по признаку Бюджет / Контракт
    if fintype != 'Контракт':
        return tmp_df[tmp_df['fintype'] != 'С оплатой обучения']
    else:
        return tmp_df[tmp_df['fintype'] == 'С оплатой обучения']

@callback(
    [Output('load_date', 'children'), Output('status_z_plot', 'figure'), Output('daily_table', 'children')],
    [Input('load_date_interval', 'n_intervals')]
)
def update_data(n):
    DATA_LOADER.load_data()
    date = datetime.datetime.strftime(DATA_LOADER.load_date, '%Y-%m-%d %H:%M')
    return date, get_status_z(), get_today_table()

def get_load_figure(counts, color, fig_type='not_cum'):

    locate_date = {  # Переименование месяца в дате
        '03': 'Март',
        '04': 'Апрель',
        '05': 'Май',
        '07': 'Июль',
        '06': 'Июнь'
    }

    counts = counts.sort_index()

    date = counts.index
    if fig_type == 'cum':

        values = counts.values.cumsum()
        title_text_yaxis = 'Суммарное число заявлений'
    else:
        values = counts.values
        title_text_yaxis = 'Число заявлений'


    new_date = []

    for dat in date:
        new_dat = str(dat).split('-')
        new_dat[1] = locate_date[new_dat[1]]
        new_date.append('-'.join(new_dat))

    fig = px.area(x=new_date, y=values, color_discrete_sequence=[color])
    fig.update_xaxes(title_text='Дата')
    fig.update_yaxes(title_text=title_text_yaxis)

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig

@callback(
    [Output('daily_load_plot', 'figure'), Output('daily_load_cum_plot', 'figure')],
    [Input("load_date_interval", 'n_intervals'), Input("pick_a_date", "start_date"), Input("pick_a_date", "end_date"), Input('type_dropdown', 'value'), Input('type_f_dropdown', 'value')]
)
def plot_daily_load(n, start, end, post_type, fintype):
    '''
    Функция отрисовывает график нагрузки по дням
    :param start: Начало периода
    :param end: Конец периода
    :param type: Тип подачи заявления
    :return: график типа area
    '''
    start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
    end = datetime.datetime.strptime(end, '%Y-%m-%d').date()

    real_df = DATA_LOADER.data
    if fintype != 'Все':
        real_df = get_df_by_fintype(real_df, fintype)

    above = real_df['add_data'] >= start
    below = real_df['add_data'] <= end

    tmp_df = real_df.loc[above & below]
    
    if post_type != 'Все':
        tmp_df = tmp_df[tmp_df['post_method'] == post_type]

    counts = pd.value_counts(tmp_df['add_data'])
    counts = counts.sort_index()

    fig = get_load_figure(counts, '#08F235', 'not_cum')
    fig_cum = get_load_figure(counts, '#0839F2', 'cum')

    return fig, fig_cum


@callback(
    Output('today_report', 'data'),
    [Input('today_report_button', "n_clicks")], prevent_initial_call=True
)
def download_today(n_clics):
    today = datetime.date.today()
    print(today)
    df = DATA_LOADER.data
    today_df = df[df['add_data'] == today]
    df_table = get_stats(today_df)
    df_table.to_excel(f'{today}.xlsx')
    return dcc.send_file(f'{today}.xlsx')

@callback(
    Output('total_report', 'data'),
    [Input('total_report_button', 'n_clicks')], prevent_initial_call=True
)
def download_total(n_clics):
    today = datetime.date.today()
    df = DATA_LOADER.data
    df_table = get_stats(df)
    df_table.to_excel(f'{today}_total.xlsx')
    return dcc.send_file(f'{today}_total.xlsx')
