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

def get_all_edu_forms(edu_level): # Все доступные формы обучения по уровню образования
    return list(DATA_LOADER.total_kcp_dict[edu_level].keys())

def get_all_specs(edu_level, edu_form): # Все доступные специальности по уровню образования
    return ['Все'] + list(DATA_LOADER.total_kcp_dict[edu_level][edu_form].keys())

def get_df_by_edu_level(df, edu_level):
    if edu_level != 'Магистратура':
        return df[df['edu_level'] != 'Магистратура']
    else:
        return df[df['edu_level'] == 'Магистратура']

def get_df_by_edu_form(tmp_df, edu_form):
    # Фильтруем по признаку Очное / Очно-Заочное / Заочное
    return tmp_df[tmp_df['edu_form'] == edu_form]

def get_df_by_fintype(tmp_df, fintype):
    # Фильтруем по признаку Бюджет / Контракт
    if fintype != 'Контракт':
        return tmp_df[tmp_df['fintype'] != 'С оплатой обучения']
    else:
        return tmp_df[tmp_df['fintype'] == 'С оплатой обучения']


control_elements = html.Div(children=[
    dcc.Interval(id='load_data_interval', interval=300e3),
    html.Br(),
    dbc.Row(children=[
        dbc.Col(children=[
            html.H3('Уровень образования'),
            dcc.Dropdown(id='edu_level_occ', options=['Бакалавриат/Специалитет', 'Магистратура'], value='Бакалавриат/Специалитет', clearable=False)
        ]),
        dbc.Col(children=[
            html.H3('Форма обучения'),
            dcc.Dropdown(id='edu_form_occ', options=['Очное', 'Очно-заочное', 'Заочное'], value='Очное', clearable=False),
        ]),
        dbc.Col(children=[
            html.H3('Форма оплаты'),
            dcc.Dropdown(id='fintype_occ', options=['Бюджет', 'Контракт'], value='Бюджет', clearable=False),
        ])
    ])
])

layout = html.Div(children=[
    control_elements,
    dcc.Graph(id='sogl_kcp_ratio_')
])


@callback(
    Output('sogl_kcp_ratio_', 'figure'),
    [Input('load_data_interval', 'n_intervals'), Input('edu_level_occ', 'value'), Input('edu_form_occ', 'value'),
     Input('fintype_occ', 'value')
     ]
)
def plot_kcp_ratio(n, edu_level, edu_form, fintype):
    df = DATA_LOADER.data
    enrolled = df[df['app_id'].notna()]

    df = get_df_by_edu_level(df, edu_level)
    df = get_df_by_edu_form(df, edu_form)
    df = get_df_by_fintype(df, fintype)

    kcp_dict = get_kcp_dict_by_edu_level(edu_level)
    kcp_dict = get_kcp_dict_by_edu_form(kcp_dict, edu_form)

    enrolled = get_df_by_edu_level(enrolled, edu_level)
    enrolled = get_df_by_edu_form(enrolled, edu_form)
    enrolled = get_df_by_fintype(enrolled, fintype)

    fintype_dict = {
        'Бюджет': 'kcp_b_all',
        'Контракт': 'kcp_k_all'
    }
    fintype = fintype_dict[fintype]

    grouped_sogl = df.groupby('spec_name', as_index=False).agg({'orig_and_agree': 'sum'})
    grouped_sogl['kcp'] = grouped_sogl.apply(lambda row: kcp_dict[row['spec_name']][fintype], axis=1)

    grouped = enrolled.groupby('spec_name', as_index=False).agg({'app_id':'count'})

    grouped_sogl = grouped_sogl.merge(grouped, on='spec_name')
    grouped_sogl['kcp_p'] = grouped_sogl['kcp'] - grouped_sogl['app_id']
    grouped_sogl = grouped_sogl[grouped_sogl['kcp'] > 0]
    grouped_sogl['Отношение кол-ва согласий к КЦП'] = grouped_sogl['orig_and_agree'] / grouped_sogl['kcp_p']
    grouped_sogl['Отношение кол-ва согласий к КЦП'] = grouped_sogl['Отношение кол-ва согласий к КЦП'].apply(lambda x: x if x < 1. else 1.)
    grouped_sogl['Запас'] = grouped_sogl['Отношение кол-ва согласий к КЦП'].apply(lambda x: 1. - x)

    grouped_sogl = grouped_sogl.sort_values('Отношение кол-ва согласий к КЦП')

    fig = px.bar(grouped_sogl, y='spec_name', x=['Отношение кол-ва согласий к КЦП', 'Запас'], orientation='h',
                 hover_data=['kcp', 'kcp_p', 'orig_and_agree'],
                 labels={'variable': 'Переменная',
                         'value': 'Значение',
                         'spec_name': 'Название специальности',
                         'kcp': 'КЦП',
                         'kcp_p': 'Основные конкурсные места',
                         'orig_and_agree': 'Согласий с оригиналом'}
                 )

    plot_h = grouped_sogl.shape[0] * 30
    if plot_h < 500:
        plot_h = 500
    fig.update_layout(
        height=plot_h,
        yaxis_title='Название специальности',
        xaxis_title="Отношение кол-ва согласий к кол-ву свободных мест"
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