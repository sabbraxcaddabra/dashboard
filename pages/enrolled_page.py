import dash
from dash import dcc
from dash import Input, Output, callback
from dash import html
import datetime
import pandas as pd
import io

import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

import os
import json

import numpy as np

import openpyxl

from . import data_loader

DATA_LOADER = data_loader.DataLoader()
DATA_LOADER.load_data()

HERE = os.path.dirname(__file__)

KCP_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "kcp.json"))
TOTAL_KCP_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "../data/total_kcp.json"))
AVERAGE_FILE = os.path.abspath(os.path.join(HERE, ".", "average.xlsx"))

df_avg: pd.DataFrame = pd.read_excel(AVERAGE_FILE)

with open(KCP_FILE, encoding='utf8') as kcp_file, open(TOTAL_KCP_FILE, encoding='utf8') as total_kcp_file:

    KCP_DICT = json.load(kcp_file)
    TOTAL_KCP_DICT: dict = json.load(total_kcp_file)


def unify_kcp(kcp_dict):

    bak = kcp_dict['Бакалавриат']
    spec = kcp_dict['Специалитет']

    bak['Очное'].update(spec['Очное'])

    return bak

def get_kcp_dict_by_edu_level(edu_level): # Словарь на уровень образование(внутри ключи - формы обучения, значения - словарь со специальностями)
    if edu_level != 'Магистратура':
        return unify_kcp(DATA_LOADER.total_kcp_dict)
    return DATA_LOADER.total_kcp_dict[edu_level]

def get_kcp_dict_by_edu_form(tmp_kcp_dict, edu_form): # Словарь на форму обуения для словаря, оставшегося при вызове предыдущей функции
    return tmp_kcp_dict[edu_form]


def datatable_settings_multiindex(df, flatten_char='_'):
    ''' Plotly dash datatables do not natively handle multiindex dataframes. This function takes a multiindex column set
    and generates a flattend column name list for the dataframe, while also structuring the table dictionary to represent the
    columns in their original multi-level format.

    Function returns the variables datatable_col_list, datatable_data for the columns and data parameters of
    the dash_table.DataTable'''

    datatable_col_list = []

    levels = df.columns.nlevels
    if levels == 1:
        for i in df.columns:
            datatable_col_list.append({"name": i, "id": i})
    else:
        columns_list = []
        for i in df.columns:
            col_id = flatten_char.join(i)
            datatable_col_list.append({"name": i, "id": col_id})
            columns_list.append(col_id)
        df.columns = columns_list

    datatable_data = df.to_dict('records')

    return datatable_col_list, datatable_data


control_elements = html.Div(children=[
    dcc.Interval(id='load_data_interval_enr', interval=100e3),
    html.Br(),
    dbc.Row(children=[
        dbc.Col(children=[
            html.H3('Уровень образования'),
            dcc.Dropdown(id='edu_level_enr', options=['Бакалавриат/Специалитет', 'Магистратура'], value='Бакалавриат/Специалитет', clearable=False)
        ]),
        dbc.Col(children=[
            html.H3('Форма обучения'),
            dcc.Dropdown(id='edu_form_enr', options=['Очное', 'Очно-заочное', 'Заочное'], value='Очное', clearable=False),
        ]),
        dbc.Col(children=[
            html.H3('Форма оплаты'),
            dcc.Dropdown(id='fintype_enr', options=['Бюджет', 'Контракт'], value='Бюджет', clearable=False),
        ])
    ])
])

layout = html.Div(children=[
    control_elements,
    dcc.Graph(id='enrolled_plot'),
    html.Div(id='enrolled_table')
])

def get_stats_plot(df: pd.DataFrame):
    grouped = df.groupby('spec_code', as_index=False).agg({
        'abiturient_id': 'count',
        'point_sum': ['mean', 'min']
    })
    grouped.columns = grouped.columns.droplevel(0)

    grouped = grouped.rename(columns={'count': 'Кол-во',
                                      'mean': 'Балл',
                                      'min': 'Проходной балл',
                                      '': 'Код специальности'})

    grouped['level'] = grouped['Код специальности'].apply(lambda x: x.split('.')[1])
    grouped = grouped.sort_values(by=['level', 'Код специальности'], ascending=False)
    grouped = grouped.drop('level', axis=1)

    grouped = grouped.round(1)

    fig = px.bar(grouped, y='Код специальности', x='Кол-во', orientation='h',
                 hover_data=list(grouped.columns))

    plot_h = grouped.shape[0] * 30
    if plot_h < 500:
        plot_h = 500
    fig.update_layout(
        height=plot_h
    )

    fig.update_traces(
        hoverlabel=dict(
            align='left',
            bgcolor="white",
            font_size=16,
            font_family="Rockwell"
        )
    )

    return fig

def get_stats_table(df):
    pivot = df.pivot_table(values='point_sum', index='spec_code',
                           columns='fintype', aggfunc=['count', 'mean'])
    pivot.columns = pivot.columns.set_names([None, 'Основания приема'])
    pivot.columns = pivot.columns.set_levels(['Кол-во', 'Балл'], level=0)
    pivot.index = pivot.index.rename('Код специальности')

    pivot = pivot.reset_index()
    pivot['level'] = pivot['Код специальности'].apply(lambda x: x.split('.')[1])
    pivot = pivot.sort_values(by=['level', 'Код специальности'])
    pivot = pivot.drop('level', axis=1)
    pivot = pivot.round(1)

    cols, data = datatable_settings_multiindex(pivot)
    table = dash.dash_table.DataTable(
        data=data, columns=cols
    )
    fig = get_stats_plot(df)

    return table, fig

def budget_stats(df, edu_level, edu_form):
    # Таблица на бюджет
    if edu_level != 'Магистратура':
        df = df[df['edu_level'] != 'Магистратура']
        df = df[df['edu_form'] == edu_form]
        return get_stats_table(df)
    else:
        df = df[df['edu_level'] == 'Магистратура']
        df = df[df['edu_form'] == edu_form]
        return get_stats_table(df)

def contract_stats(df, edu_level, edu_form):
    # Таблица на контракт
    if edu_level != 'Магистратура':
        df = df[df['edu_level'] != 'Магистратура']
        df = df[df['edu_form'] == edu_form]
        return get_stats_table(df)
    else:
        df = df[df['edu_level'] == 'Магистратура']
        df = df[df['edu_form'] == edu_form]
        return get_stats_table(df)

@callback(
    [Output('enrolled_table', 'children'), Output('enrolled_plot', 'figure')],
    [Input('load_data_interval_enr', 'n_intervals'), Input('edu_level_enr', 'value'), Input('edu_form_enr', 'value'),
     Input('fintype_enr', 'value')
     ]
)
def get_stats(n, edu_level, edu_form, fintype):
    df = DATA_LOADER.data
    df = df[df['decree_id'].notna()]
    if fintype == 'Бюджет':
        df = df[df['fintype'] != 'С оплатой обучения']
        return budget_stats(df, edu_level, edu_form)
    else:
        df = df[df['fintype'] == 'С оплатой обучения']
        return contract_stats(df, edu_level, edu_form)
