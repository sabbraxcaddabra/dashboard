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
    os_spec: pd.DataFrame = df[(df['fintype'] == 'Особая квота') | (df['fintype'] == 'Специальная квота')]

    celo_grouped = celo.groupby(['spec_name', 'spec_code'], as_index=False).agg({'abiturient_id': 'count', 'point_sum': 'mean'})
    os_spec_grouped = os_spec.groupby(['spec_name', 'spec_code'], as_index=False).agg({'abiturient_id': 'count', 'point_sum': 'mean'})

    grouped = celo_grouped.merge(os_spec_grouped, how='outer', on='spec_name', suffixes=('_celo', '_os_spec'))

    return grouped

def get_fst_w_stats(df: pd.DataFrame):

    fst_w_grouped = df.groupby(['spec_name', 'spec_code'], as_index=False).agg({'abiturient_id': 'count', 'point_sum': 'mean'})

    return fst_w_grouped


def get_bak_spec_fst_w(df): # Бакалавриат/Специалитет - Очное - Бюджет первая волна
    df = get_df_by_edu_level(df, 'Бакалавриат/Специалитет')
    df = get_df_by_edu_form(df, 'Очное')
    df = get_df_by_fintype(df, 'Бюджет')

    df = df.query("decree_id == 9")

    return df

def get_bak_spec_sec_w(df): # Бакалавриат/Специалитет - Очное - Бюджет вторая волна
    df = get_df_by_edu_level(df, 'Бакалавриат/Специалитет')
    df = get_df_by_edu_form(df, 'Очное')
    df = get_df_by_fintype(df, 'Бюджет')

    df = df[df['fintype'] == 'Основные места']
    df = df[df['decree_id'].isna()]
    df = df[df['orig_and_agree'] == 1]

    return df[df['orig_and_agree'] == 1], df

def get_sec_w_stats(df):
    sec_w_grouped = df.groupby(['spec_name', 'spec_code'], as_index=False).agg({'abiturient_id': 'count', 'point_sum': 'mean'})

    return sec_w_grouped

def get_were_in_k(dec_id):
    print(dec_id)
    if dec_id:
        return 1
    else:
        return 0

def get_total_stats(prior_df, fst_w_df, sec_w_df, df_not_orig, df):

    df = get_df_by_edu_level(df, 'Бакалавриат/Специалитет')
    df = get_df_by_edu_form(df, 'Очное')
    df = get_df_by_fintype(df, 'Бюджет')

    enrolled = df[df['decree_id'].notna()]['abiturient_id'].to_list()

    df['were_in_k'] = df['abiturient_id'].apply(lambda ab_id: 1 if ab_id in enrolled else 0)

    ab_grouped = df.groupby('abiturient_id', as_index=True).agg({'were_in_k': 'sum'})
    ab_grouped = ab_grouped[ab_grouped['were_in_k'] > 0]

    df['were_in_k'] = df.apply(lambda row: row['abiturient_id'] in ab_grouped.index.to_list(), axis=1)
    not_in_k = df[df['were_in_k'] == False]
    zapas = not_in_k.groupby('spec_name', as_index=False).agg({'abiturient_id': 'nunique'})

    total_df = pd.concat((prior_df, fst_w_df, sec_w_df), ignore_index=True)
    total_grouped = total_df.groupby(['spec_name', 'spec_code'], as_index=False).agg({'abiturient_id': 'count', 'point_sum': 'mean'})

    zapas = zapas.rename(columns={
        'abiturient_id': 'zapas'
    })

    total_grouped = total_grouped.merge(zapas, how='left', on='spec_name')

    return total_df, total_grouped

layout = html.Div(children=[
    dcc.Interval(id='load_data_fst_w', interval=500e3),
    # dcc.Graph(id='fst_w_plot'),
    html.Div(id='fst_w_table'),
    html.Br(),
    html.Br()
])


def get_were_in_k(decree_id):
    if decree_id:
        return 1
    return 0

def get_bak_spec_table(df):
    df_prior = get_bak_spec_prior(df)
    df_fst_w = get_bak_spec_fst_w(df)
    df_sec_w, df_not_orig = get_bak_spec_sec_w(df)
    kcp_dict = get_kcp_dict_by_edu_level('Бакалавриат/Специалитет')
    kcp_dict = get_kcp_dict_by_edu_form(kcp_dict, 'Очное')

    prior_stats = get_prior_stats(df_prior)
    fst_w_stats = get_fst_w_stats(df_fst_w)
    sec_w_stats = get_sec_w_stats(df_sec_w)

    # prior_stats.to_excel('prior.xlsx')

    osn_k_grouped = fst_w_stats.merge(sec_w_stats, how='outer', on='spec_name', suffixes=('_fst_w', '_sec_w'))
    total_df, total_stats = get_total_stats(df_prior, df_fst_w, df_sec_w, df_not_orig, df)

    grouped = osn_k_grouped.merge(prior_stats, how='outer', on='spec_name')
    grouped['kcp'] = grouped.apply(lambda row: kcp_dict[row['spec_name']]['kcp_b_all'], axis=1)

    grouped = grouped.fillna(value={
        'abiturient_id_celo': 0,
        'abiturient_id_os_spec': 0,
        'abiturient_id_fst_w': 0
    })

    grouped['kcp_p'] = grouped['kcp'] - grouped['abiturient_id_celo'] - grouped['abiturient_id_os_spec'] - grouped['abiturient_id_fst_w']

    grouped = total_stats.merge(grouped, how='outer', on='spec_name')

    needed_cols = ['spec_code_fst_w', 'spec_name',
                   'abiturient_id', 'point_sum',
                   'abiturient_id_celo', 'point_sum_celo',
                   'abiturient_id_os_spec', 'point_sum_os_spec',
                   'abiturient_id_fst_w', 'point_sum_fst_w',
                   'abiturient_id_sec_w', 'point_sum_sec_w',
                   'kcp_p', 'zapas'
                   ]

    grouped = grouped.loc[:, needed_cols].rename(columns={
        'spec_code_fst_w': 'Код специальности', 'spec_name': 'Название направления подготовки',
        'abiturient_id': 'Бюджет в рамках КЦП', 'point_sum': 'Бюджет в рамках КЦП, балл',
        'abiturient_id_celo': 'Целевая квота', 'point_sum_celo': 'Целевая квота, балл',
        'abiturient_id_os_spec': 'Особая и спец. квота', 'point_sum_os_spec': 'Особая и спец. квота, балл',
        'abiturient_id_fst_w': 'Основные места 1 волна', 'point_sum_fst_w': 'Основные места 1 волна, балл',
        'abiturient_id_sec_w': 'Основные места 2 волна', 'point_sum_sec_w': 'Основные места 2 волна, балл',
        'kcp_p': 'Остаток до закрытия КЦП', 'zapas': 'Запас по заялениям'
    })

    grouped = grouped.round(1)

    table = dash.dash_table.DataTable(
        data=grouped.to_dict('records'),
        style_cell={'font_size': '12px',
                    'text_align': 'center'
                    },
        export_format='xlsx',
        export_headers='display',
        sort_action="native"
    )

    return table

@callback(
    Output('fst_w_table', 'children'),
    [Input('load_data_fst_w', 'n_intervals')]
)
def plot_bak_spec(n):

    df = DATA_LOADER.load_data()
    return get_bak_spec_table(df)
    # df_prior = get_bak_spec_prior(df)
    # df_fst_w = get_bak_spec_fst_w(df)
    # df_sec_w = get_bak_spec_sec_w(df)
    # kcp_dict = get_kcp_dict_by_edu_level('Бакалавриат/Специалитет')
    # kcp_dict = get_kcp_dict_by_edu_form(kcp_dict, 'Очное')
    #
    # prior_stats = get_prior_stats(df_prior)
    # fst_w_stats = get_fst_w_stats(df_fst_w)
    # sec_w_stats = get_sec_w_stats(df_sec_w)
    #
    # osn_k_grouped = fst_w_stats.merge(sec_w_stats, on='spec_name', suffixes=('fst_w', 'sec_w'))
    #
    # grouped = prior_stats.merge(osn_k_grouped, how='left', on='spec_name')
    # grouped['kcp'] = grouped.apply(lambda row: kcp_dict[row['spec_name']]['kcp_b_all'], axis=1)
    # grouped.to_excel('fst_w.xlsx')
    # return 'Тут скоро будет таблица'