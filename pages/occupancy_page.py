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

def get_edu_level(spec_code):
    splitted = spec_code.split('.')
    return splitted[1]

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
    dcc.Interval(id='load_data_interval_', interval=100e3),
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
    html.A("Ссылка на статистику траектории",
           href='http://library.voenmeh.ru/jirbis2/files/priem2022/traectory_stat.html',
           target="_blank"
           ),
    dcc.Graph(id='sogl_kcp_ratio_'),
    html.Div(id='zapol_table')
])


def get_minimum_bal(df: pd.DataFrame, spec_name, kcp_p):
    df = df[df['spec_name'] == spec_name]
    df = df[df['orig_and_agree'] == 1]
    df = df[df['app_id'].isna()]
    df = df.sort_values('point_sum', ascending=False)
    if df.shape[0] > kcp_p:
        df = df.iloc[:int(kcp_p)]
        return df['point_sum'].min()
    else:
        return df['point_sum'].min()

def get_bak_spec_prior(df): # Бакалавриат/Специалитет - Очное - Бюджет приоритетный этап
    df = get_df_by_edu_level(df, 'Бакалавриат/Специалитет')
    df = get_df_by_edu_form(df, 'Очное')
    df = get_df_by_fintype(df, 'Бюджет')

    df = df.query("decree_id in (3, 4, 5, 6)")

    return df

def get_prior_stats(df: pd.DataFrame):
    celo: pd.DataFrame = df[df['fintype'] == 'Целевая квота']
    os_spec: pd.DataFrame = df[df['fintype'] != 'Целевая квота']

    celo_grouped = celo.groupby(['spec_name', 'spec_code'], as_index=False).agg({'abiturient_id': 'count', 'point_sum': 'mean'})
    os_spec_grouped = os_spec.groupby(['spec_name', 'spec_code'], as_index=False).agg({'abiturient_id': 'count', 'point_sum': 'mean'})

    grouped = celo_grouped.merge(os_spec_grouped, how='left', on='spec_name', suffixes=('_celo', '_os_spec'))

    return grouped

def get_fst_w_stats(df: pd.DataFrame):

    fst_w_grouped = df.groupby(['spec_name', 'spec_code'], as_index=False).agg({'abiturient_id': 'count', 'point_sum': 'mean'})

    return fst_w_grouped


def test_prior(df):
    df = get_bak_spec_prior(df)
    print(get_prior_stats(df))


def get_bak_spec_fst_w(df): # Бакалавриат/Специалитет - Очное - Бюджет первая волна
    df = get_df_by_edu_level(df, 'Бакалавриат/Специалитет')
    df = get_df_by_edu_form(df, 'Очное')
    df = get_df_by_fintype(df, 'Бюджет')

    df = df.query("decree_id == 9")

    return df

def plot_bak_spec(df):
    df_prior = get_bak_spec_prior(df)
    df_fst_w = get_bak_spec_fst_w(df)
    kcp_dict = get_kcp_dict_by_edu_level('Бакалавриат/Специалитет')
    kcp_dict = get_kcp_dict_by_edu_form(kcp_dict, 'Очное')

    prior_stats = get_prior_stats(df_prior)
    fst_w_stats = get_fst_w_stats(df_fst_w)

    grouped = prior_stats.merge(fst_w_stats, how='left', on='spec_name', suffixes=('', '_sft_w'))
    # grouped.to_excel('fst_w.xlsx')
    # print(grouped)


@callback(
    [Output('sogl_kcp_ratio_', 'figure'), Output('zapol_table', 'children')],
    [Input('load_data_interval_', 'n_intervals'), Input('edu_level_occ', 'value'), Input('edu_form_occ', 'value'),
     Input('fintype_occ', 'value')
     ]
)
def plot_kcp_ratio(n, edu_level, edu_form, fintype):
    DATA_LOADER.load_data()
    df = DATA_LOADER.data

    plot_bak_spec(df)
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

    labels_dict = {
        'Бюджет': ['КЦП', 'Основные конкурсные места'],
        'Контракт': ['ДОУ', 'Оставшиеся места']
    }

    labels = labels_dict[fintype]

    fintype_ = fintype_dict[fintype]

    df = df[df['app_id'].isna()]
    df['point_sum'] = df['point_sum'] + df['ach']

    grouped_sogl = df.groupby(['spec_name', 'spec_code'], as_index=False).agg({'orig_and_agree': 'sum'})
    grouped_sogl['kcp'] = grouped_sogl.apply(lambda row: kcp_dict[row['spec_name']][fintype_], axis=1)

    grouped = enrolled.groupby('spec_name', as_index=False).agg({'app_id':'count'})

    grouped_sogl = grouped_sogl.merge(grouped, how='left', on='spec_name')
    grouped_sogl = grouped_sogl.fillna(0.)

    grouped_sogl['kcp_p'] = grouped_sogl['kcp'] - grouped_sogl['app_id']
    grouped_sogl['min_point'] = grouped_sogl.apply(lambda row: get_minimum_bal(df, row['spec_name'], row['kcp_p']), axis=1)
    grouped_sogl = grouped_sogl[grouped_sogl['kcp'] > 0]
    grouped_sogl['Заполняемость'] = grouped_sogl['orig_and_agree'] / grouped_sogl['kcp_p']
    grouped_sogl['Заполняемость'] = grouped_sogl['Заполняемость'].apply(lambda x: x if x < 1. else 1.) * 100
    grouped_sogl['Остаток'] = grouped_sogl['Заполняемость'].apply(lambda x: 100. - x)

    grouped_sogl['Заполняемость'] = grouped_sogl['Заполняемость'].apply(lambda x: round(x, 1))
    grouped_sogl['Остаток'] = grouped_sogl['Остаток'].apply(lambda x: round(x, 1))

    grouped_sogl['level_code'] = grouped_sogl['spec_code'].apply(get_edu_level)
    grouped_sogl = grouped_sogl.sort_values(['level_code', 'spec_code'], ascending=False)
    grouped_sogl['spec_name_1'] = grouped_sogl.apply(lambda row: f'{row["spec_name"]} {row["spec_code"]}', axis=1)

    if fintype == 'Контракт':
        hover_data = ['kcp', 'kcp_p', 'orig_and_agree']
    else:
        hover_data = ['kcp', 'kcp_p', 'orig_and_agree', 'min_point']

    fig = px.bar(grouped_sogl, y='spec_name_1', x=['Заполняемость', 'Остаток'], orientation='h',
                 hover_data=hover_data,
                 labels={'variable': 'Переменная',
                         'value': 'Значение, %',
                         'spec_name_1': 'Название специальности',
                         'kcp': labels[0],
                         'kcp_p': labels[1],
                         'orig_and_agree': 'Согласий с оригиналом',
                         'min_point': 'Проходной балл'
                         }
                 )

    plot_h = grouped_sogl.shape[0] * 30
    if plot_h < 500:
        plot_h = 500
    fig.update_layout(
        height=plot_h,
        yaxis_title='Название специальности',
        xaxis_title="Заполняемость, %"
    )

    fig.update_traces(
        hoverlabel=dict(
            align='left',
            bgcolor="white",
            font_size=16,
            font_family="Rockwell"
        )
    )

    grouped_sogl = grouped_sogl.rename(
        columns={
            'spec_name': 'Название специальности',
            'kcp_p': labels[1],
            'min_point': 'Проходной балл',
            'spec_code': 'Код специальности',
            'Заполняемость': 'Заполняемость, %',
            'Остаток': 'Остаток, %'
        }
    )

    if fintype == 'Контракт':
        loc_list = ['Название специальности', 'Код специальности', labels[1], 'Заполняемость, %', 'Остаток, %']
    else:
        loc_list = ['Название специальности', 'Код специальности', labels[1], 'Заполняемость, %', 'Остаток, %', 'Проходной балл']

    grouped_sogl = grouped_sogl.loc[:, loc_list]
    grouped_sogl = grouped_sogl.sort_values(['Название специальности', 'Код специальности'], ascending=False)

    table = dash.dash_table.DataTable(
        data=grouped_sogl.to_dict('records'),
        style_cell={'font_size': '14px',
                    'text_align': 'center'
                    },
        sort_action="native"
    )

    return fig, table