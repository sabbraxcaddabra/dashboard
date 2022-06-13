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
import json

import numpy as np


bac_spec_b_header = [
    {'name': ['', 'Код'], 'id': 'spec_code'},
    {'name': ['', 'Направление подготовки'], 'id': 'spec_name'},
    {'name': ['', 'Заявлений всего'], 'id': 'all_application'},
    {'name': ['', 'Средний балл'], 'id': 'mean_bal'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Всего'], 'id': 'orig_all'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Основные места'], 'id': 'orig_osn'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Целевая квота'], 'id': 'orig_cel'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Особая квота'], 'id': 'orig_os'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Специальная квота'], 'id': 'orig_spec'},
]

bac_spec_k_header = [
    {'name': ['', 'Код'], 'id': 'spec_code'},
    {'name': ['', 'Направление подготовки'], 'id': 'spec_name'},
    {'name': ['', 'Заявлений всего'], 'id': 'all_application'},
    {'name': ['', 'Средний балл'], 'id': 'mean_bal'},
    {'name': ['Оригинал документа об образовании (в скобках места по Доу)', 'Всего'], 'id': 'orig_all'},
]

mag_b_header = [
    {'name': ['', 'Код'], 'id': 'spec_code'},
    {'name': ['', 'Профиль магистратуры'], 'id': 'spec_name'},
    {'name': ['', 'Заявлений всего'], 'id': 'all_application'},
    {'name': ['', 'Средний балл'], 'id': 'mean_bal'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Всего'], 'id': 'orig_all'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Основные места'], 'id': 'orig_osn'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Целевая квота'], 'id': 'orig_cel'},
]

mag_k_header = [
    {'name': ['', 'Код'], 'id': 'spec_code'},
    {'name': ['', 'Профиль магистратуры'], 'id': 'spec_name'},
    {'name': ['', 'Заявлений всего'], 'id': 'all_application'},
    {'name': ['', 'Средний балл'], 'id': 'mean_bal'},
    {'name': ['Оригинал документа об образовании (в скобках места по ДОУ)', 'Всего'], 'id': 'orig_all'},
]

bak_spec_default_dict = {
   'spec_code': '24.03.03',
   'spec_name': 'Баллистика и гидроаэродинамика',
   'kcp_k': 4,
   'kcp_os': 2,
   'kcp_spec': 2,
   'kcp_cel': 4,
   'kcp_osn': 12
}

mags_default_dict = {
   'spec_code': '09.04.01',
   'spec_name': 'Интеллектуальные системы',
   'kcp_k': 2,
   'kcp_cel': 0,
   'kcp_osn': 5
}

HERE = os.path.dirname(__file__)
DATA_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "stats.xlsx"))
KCP_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "kcp.json"))

df = pd.read_excel(DATA_FILE)

SPEC_TABLE_COLUMNS = [
    {'name': ['', 'Код'], 'id': 'spec_code'},
    {'name': ['', 'Направление подготовки'], 'id': 'spec_name'},
    {'name': ['', 'Заявлений всего'], 'id': 'all_application'},
    {'name': ['', 'Средний балл'], 'id': 'mean_bal'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Всего'], 'id': 'orig_all'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Основные места'], 'id': 'orig_osn'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Целевая квота'], 'id': 'orig_cel'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Особая квота'], 'id': 'orig_os'},
    {'name': ['Оригинал документа об образовании (в скобках КЦП)', 'Специальная квота'], 'id': 'orig_spec'},
]

DEFAULT_DICT = {'spec_code': '24.03.03',
   'spec_name': 'Баллистика и гидроаэродинамика',
   'kcp_k': 4,
   'kcp_os': 2,
   'kcp_spec': 2,
   'kcp_cel': 4,
   'kcp_osn': 12
}

with open(KCP_FILE, encoding='utf8') as kcp_file:
    KCP_DICT = json.load(kcp_file)


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

# name_frequency = html.Div(children=[ # График с распределением по заявлениям
#     dcc.Graph(figure=get_spec_frec(), id='spec_hist')
# ])

control_elements = html.Div(children=[
    dbc.Row(children=[
        dbc.Col(children=[
            html.H3('Уровень образования'),
            dcc.Dropdown(id='edu_level', options=['Бакалавриат', 'Специалитет', 'Магистратура'], value='Бакалавриат', clearable=False)
        ]),
        dbc.Col(children=[
            html.H3('Форма оплаты'),
            dcc.Dropdown(id='fin_type', options=['Бюджет', 'Контракт'], value='Бюджет', clearable=False),
        ])
    ])
])

mean_point = html.Div(children=[ # Блок с распределением среднего балла по специальностям
    dbc.Row(children=[
        dbc.Col(children=[
            html.H5('Направление подготовки'),
            dcc.Dropdown(id='spec_names', clearable=False)
        ], width=6)
    ]),
    html.Div(id='info_table'),
    html.Div(children=[
        dcc.Graph(id='kvots_plot')
    ], id='kvots_div'),
    html.H3('Распределение по баллам'),
    html.Div('*С учетом выбранных настроек'),
    html.H5('Диапазон баллов'),
    dcc.RangeSlider(40, 100, 5, value=[50, 100], id='bal_range'),
    dcc.Graph(id='mean_point_plot')
])

agree_ratio = html.Div(children=[
    html.H3('Соотношение числа согласий к общему числу заявлений'),
    html.Div('*С учетом выбранных настроек'),
    dcc.Graph(id='agree_ratio_plot')
])

dop_info = html.Div(children=[
    html.H3('Дополнительная статистика'),
    html.Div('*Учитывается только выбранное направление подготовки'),
    html.H3('Распределение по регионам (СПБ и ЛО приведены отдельно)'),
    html.Div(id='spb_lo', style={'marginRight': 700}),
    dcc.Graph(id='regio_plot'),
    html.H3('Распределение по гражданству (кроме граждан РФ)'),
    dcc.Graph(id='citiz_plot'),
    html.H3('Соотношение поступающих мужского и женского пола'),
    dcc.Graph(id='gender_plot'),
])

layout = html.Div(children=[
    control_elements,
    mean_point,
    agree_ratio,
    dop_info
])

@callback(
    [Output('kvots_plot', 'figure'), Output('kvots_div', 'style')],
    [Input('edu_level', 'value'), Input('fin_type', 'value'), Input('spec_names', 'value')]
)
def get_kvots_plot(edu_level, fin_type, spec_name):
    if edu_level == 'Магистратура' or fin_type == 'Контракт':

        return go.Figure(), {'display':'none'}
    else:
        tmp_df = get_df_by_edu_level(df, edu_level)
        tmp_df = get_df_by_fintype(tmp_df, fin_type)
        tmp_df = get_df_by_spec_name(tmp_df, spec_name)
        counts = pd.value_counts(tmp_df['finance_type'])
        tmp_df = pd.DataFrame(data={'Форма оплаты': counts.index, 'Количество': counts.values})

        fig = px.pie(tmp_df, names='Форма оплаты', values='Количество', height=600, title='Распределение количества заявлений по соответсвующим формам оплаты')

        return fig, {'display':'block'}




@callback(
    Output('info_table', 'children'),
    [Input('edu_level', 'value'), Input('fin_type', 'value'), Input('spec_names', 'value')]
)
def get_info_table(edu_level, fin_type, spec_name):

    tmp_df = get_df_by_edu_level(df, edu_level)
    tmp_df = get_df_by_fintype(tmp_df, fin_type)

    if edu_level != 'Магистратура':
        return get_bak_spec_table(tmp_df, edu_level, fin_type, spec_name)
    else:
        return get_mag_table(tmp_df, edu_level, fin_type, spec_name)

def get_header(edu_level, fin_type):
    headers_dict = {
        'Бакалавриат': {'Бюджет': bac_spec_b_header, 'Контракт': bac_spec_k_header},
        'Специалитет': {'Бюджет': bac_spec_b_header, 'Контракт': bac_spec_k_header},
        'Магистратура': {'Бюджет': mag_b_header, 'Контракт': mag_k_header},
    }
    return headers_dict[edu_level][fin_type]

def get_bak_spec_table(tmp_df, edu_level, fin_type, spec_name):

    header = get_header(edu_level, fin_type)
    fin_type_dict = {'Бюджет': get_bak_spec_b_table_data, 'Контракт': get_bak_spec_k_table_data}
    table_func = fin_type_dict[fin_type]

    if spec_name == 'Все':
        specs = tmp_df['specName'].unique()
        data = []
        for spec in specs:
            spec_dict = table_func(tmp_df, edu_level, spec)
            data.append(spec_dict)
    else:
        data = [table_func(tmp_df, edu_level, spec_name)]

    if spec_name == 'Все':
        export_kwargs = dict(export_headers='display', export_format='xlsx')
    else:
        export_kwargs = dict()

    return dash.dash_table.DataTable(
        columns=header,
        data=data,
        merge_duplicate_headers=True,
        style_cell={'font_size': '16px',
                    'text_align': 'left'
                    },
        **export_kwargs
    )


def get_mag_table(tmp_df, edu_level, fin_type, spec_name):
    header = get_header(edu_level, fin_type)
    fin_type_dict = {'Бюджет': get_mags_b_table_data, 'Контракт': get_mags_k_table_data}
    table_func = fin_type_dict[fin_type]

    if spec_name == 'Все':
        specs = tmp_df['specName'].unique()
        data = []
        for spec in specs:
            spec_dict = table_func(tmp_df, spec)
            data.append(spec_dict)
    else:
        data = [table_func(tmp_df, spec_name)]

    if spec_name == 'Все':
        export_kwargs = dict(export_headers='display', export_format='xlsx')
    else:
        export_kwargs = dict()

    return dash.dash_table.DataTable(
        columns=header,
        data=data,
        merge_duplicate_headers=True,
        style_cell={'font_size': '16px',
                    'text_align': 'left'
                    },
        **export_kwargs
    )


@callback(
    [Output('spec_names', 'options'), Output('spec_names', 'value')],
    [Input('edu_level', 'value'), Input('fin_type', 'value')]
)
def get_spec_names(edu_level, fin_type):
    tmp_df = get_df_by_edu_level(df, edu_level)
    tmp_df = get_df_by_fintype(tmp_df, fin_type)
    specs = ['Все'] + list(tmp_df['specName'].unique())

    return specs, 'Все'

def get_mags_b_table_data(tmp_df, spec_name): # Таблица на магистратуру бюджет

    tmp_tmp_df = tmp_df[tmp_df['specName'] == spec_name]
    mean_bal = tmp_tmp_df['point_mean'].mean()
    applications = tmp_tmp_df.shape[0]
    orig_all = pd.value_counts(tmp_tmp_df['abAgr']).get(1, 0)
    orig_osn = pd.value_counts(tmp_tmp_df[tmp_tmp_df['finance_type'] == 'Основные места']['abAgr']).get(1, 0)
    orig_cel = pd.value_counts(tmp_tmp_df[tmp_tmp_df['finance_type'] == 'Целевая квота']['abAgr']).get(1, 0)

    kcp_dict = KCP_DICT['mag'].get(spec_name, mags_default_dict)
    kcp_all = kcp_dict['kcp_osn'] + kcp_dict['kcp_cel']
    spec_dict = {
        'spec_code': kcp_dict['spec_code'],
        'spec_name': kcp_dict['spec_name'],
        'all_application': applications,
        'mean_bal': round(mean_bal, 2),
        'orig_all': f'{orig_all} ({kcp_all})',
        'orig_osn': f'{orig_osn} ({kcp_dict["kcp_osn"]})',
        'orig_cel': f'{orig_cel} ({kcp_dict["kcp_cel"]})'
    }
    return spec_dict

def get_mags_k_table_data(tmp_df, spec_name): # Таблица на магистратуру контракт

    tmp_tmp_df = tmp_df[tmp_df['specName'] == spec_name]
    mean_bal = tmp_tmp_df['point_mean'].mean()
    applications = tmp_tmp_df.shape[0]
    orig_all = pd.value_counts(tmp_tmp_df['abAgr']).get(1, 0)

    kcp_dict = KCP_DICT['mag'].get(spec_name, mags_default_dict)
    spec_dict = {
        'spec_code': kcp_dict['spec_code'],
        'spec_name': kcp_dict['spec_name'],
        'all_application': applications,
        'mean_bal': round(mean_bal, 2),
        'orig_all': f'{orig_all} ({kcp_dict["kcp_k"]})'
    }
    return spec_dict

def get_bak_spec_b_table_data(tmp_df, edu_level, spec_name): # Таблица на бакалавриат / специалитет бюджет
    edu_level_dict = {
        'Бакалавриат': 'bac',
        'Специалитет': 'spec'
    }

    edu_level = edu_level_dict[edu_level]
    tmp_tmp_df = tmp_df[tmp_df['specName'] == spec_name]
    mean_bal = tmp_tmp_df['point_mean'].mean()
    applications = tmp_tmp_df.shape[0]
    orig_all = pd.value_counts(tmp_tmp_df['abAgr']).get(1, 0)
    orig_osn = pd.value_counts(tmp_tmp_df[tmp_tmp_df['finance_type'] == 'Основные места']['abAgr']).get(1, 0)
    orig_cel = pd.value_counts(tmp_tmp_df[tmp_tmp_df['finance_type'] == 'Целевая квота']['abAgr']).get(1, 0)
    orig_os = pd.value_counts(tmp_tmp_df[tmp_tmp_df['finance_type'] == 'Особая квота']['abAgr']).get(1, 0)
    orig_spec = pd.value_counts(tmp_tmp_df[tmp_tmp_df['finance_type'] == 'Специальная квота']['abAgr']).get(1, 0)
    kcp_dict = KCP_DICT[edu_level].get(spec_name, bak_spec_default_dict)
    kcp_all = kcp_dict['kcp_osn'] + kcp_dict['kcp_os'] + kcp_dict['kcp_spec'] + kcp_dict['kcp_cel']
    spec_dict = {
        'spec_code': kcp_dict['spec_code'],
        'spec_name': kcp_dict['spec_name'],
        'all_application': applications,
        'mean_bal': round(mean_bal, 2),
        'orig_all': f'{orig_all} ({kcp_all})',
        'orig_osn': f'{orig_osn} ({kcp_dict["kcp_osn"]})',
        'orig_cel': f'{orig_cel} ({kcp_dict["kcp_cel"]})',
        'orig_os': f'{orig_os} ({kcp_dict["kcp_os"]})',
        'orig_spec': f'{orig_spec} ({kcp_dict["kcp_spec"]})',
    }
    return spec_dict

def get_bak_spec_k_table_data(tmp_df, edu_level, spec_name): # Таблица на бакалавриат / специалитет контракт
    edu_level_dict = {
        'Бакалавриат': 'bac',
        'Специалитет': 'spec'
    }

    edu_level = edu_level_dict.get(edu_level, 'bac')

    tmp_tmp_df = tmp_df[tmp_df['specName'] == spec_name]
    mean_bal = tmp_tmp_df['point_mean'].mean()
    applications = tmp_tmp_df.shape[0]
    orig_all = pd.value_counts(tmp_tmp_df['abAgr']).get(1, 0)
    kcp_dict = KCP_DICT[edu_level].get(spec_name, bak_spec_default_dict)
    spec_dict = {
        'spec_code': kcp_dict['spec_code'],
        'spec_name': kcp_dict['spec_name'],
        'all_application': applications,
        'mean_bal': round(mean_bal, 2),
        'orig_all': f'{orig_all} ({kcp_dict["kcp_k"]})',
    }
    return spec_dict

def get_spec_table_data(tmp_df, edu_level, spec_name):

    edu_level_dict = {
        'Бакалавриат': 'bac',
        'Специалитет': 'spec'
    }

    edu_level = edu_level_dict.get(edu_level, 'bac')

    tmp_tmp_df = tmp_df[tmp_df['specName'] == spec_name]
    mean_bal = tmp_tmp_df['point_mean'].mean()
    applications = tmp_tmp_df.shape[0]
    orig_all = pd.value_counts(tmp_tmp_df['abAgr'])[1]
    orig_osn = pd.value_counts(tmp_tmp_df[tmp_tmp_df['finance_type'] == 'Основные места']['abAgr']).get(1, 0)
    orig_cel = pd.value_counts(tmp_tmp_df[tmp_tmp_df['finance_type'] == 'Целевая квота']['abAgr']).get(1, 0)
    orig_os = pd.value_counts(tmp_tmp_df[tmp_tmp_df['finance_type'] == 'Особая квота']['abAgr']).get(1, 0)
    orig_spec = pd.value_counts(tmp_tmp_df[tmp_tmp_df['finance_type'] == 'Специальная квота']['abAgr']).get(1, 0)
    kcp_dict = KCP_DICT[edu_level].get(spec_name, bak_spec_default_dict)
    kcp_all = kcp_dict['kcp_osn'] + kcp_dict['kcp_os'] + kcp_dict['kcp_spec'] + kcp_dict['kcp_cel']
    spec_dict = {
        'spec_code': kcp_dict['spec_code'],
        'spec_name': kcp_dict['spec_name'],
        'all_application': applications,
        'mean_bal': round(mean_bal, 2),
        'orig_all': f'{orig_all} ({kcp_all})',
        'orig_osn': f'{orig_osn} ({kcp_dict["kcp_osn"]})',
        'orig_cel': f'{orig_cel} ({kcp_dict["kcp_cel"]})',
        'orig_os': f'{orig_os} ({kcp_dict["kcp_os"]})',
        'orig_spec': f'{orig_spec} ({kcp_dict["kcp_spec"]})',
    }
    return spec_dict


def get_df_by_fintype(tmp_df, fintype):
    # Фильтруем по признаку Бюджет / Контракт
    if fintype != 'Контракт':
        return tmp_df[tmp_df['finance_type'] != 'С оплатой обучения']
    else:
        return df[df['finance_type'] == 'С оплатой обучения']

def get_df_by_edu_level(tmp_df, edu_level):
    # Фильтруем по признаку Бакалавриат / Специалитет / Магистратура
    return tmp_df[tmp_df['edu_form'] == edu_level]

def get_df_by_spec_name(tmp_df, spec_name):
    if spec_name != 'Все':
        return tmp_df[tmp_df['specName'] == spec_name]
    else:
        return tmp_df



@callback(
    Output('mean_point_plot', 'figure'),
    [Input('edu_level', 'value'), Input('fin_type', 'value'), Input('spec_names', 'value'),
     Input('bal_range', 'value')
     ]
)
def update_mean_point_plot(edu_level, fin_type, spec_name, bal_range):

    tmp_df = get_df_by_edu_level(df, edu_level)
    tmp_df = get_df_by_fintype(tmp_df, fin_type)
    tmp_df = get_df_by_spec_name(tmp_df, spec_name)


    tmp_df = tmp_df[(tmp_df['point_mean'] > bal_range[0]) & (tmp_df['point_mean'] < bal_range[1])]

    fig = px.histogram(data_frame=tmp_df, x='point_mean', nbins=25, marginal='box')
    fig.update_layout(bargap=0.1)

    fig.update_layout(
        xaxis_title="Средний балл",
        yaxis_title="Количество заявлений"
    )
    return fig

@callback(
    Output('agree_ratio_plot', 'figure'),
    [Input('edu_level', 'value'), Input('fin_type', 'value'), Input('spec_names', 'value'),
     Input('bal_range', 'value')
     ]
)
def agree_ratio(edu_level, fin_type, spec_name, bal_range): # Отношение числа согласных к общему числу заявлений

    tmp_df = get_df_by_edu_level(df, edu_level)
    tmp_df = get_df_by_fintype(tmp_df, fin_type)
    tmp_df = get_df_by_spec_name(tmp_df, spec_name)

    tmp_df = tmp_df[(tmp_df['point_mean'] > bal_range[0]) & (tmp_df['point_mean'] < bal_range[1])]

    agree = tmp_df[tmp_df['abAgr'] == 1]

    mean_z = tmp_df['point_mean'].mean()  # Средний балл заявления

    agree_mean = agree['point_mean'].mean()  # Средний балл согласия

    counts, bins = np.histogram(agree['point_mean'], bins=range(*bal_range, 2))

    bins = 0.5 * (bins[:-1] + bins[1:])

    counts = counts / tmp_df.shape[0] if tmp_df.shape[0] != 0 else counts

    fig = px.bar(x=bins, y=counts, labels={'x': 'Средний балл', 'y': 'Отношение числа согласий к общему числу заявлений'}, height=650)

    return fig

@callback(
    Output('spb_lo', 'children'),
    [Input('spec_names', 'value')]
)
def update_spb_lo(spec_name):

    tmp_df = get_df_by_spec_name(df, spec_name)

    tmp_df = tmp_df[(tmp_df['regio'] == 'СПБ') | (tmp_df['regio'] == 'ЛО')]

    counts = pd.value_counts(tmp_df['regio'])
    spb = counts['СПБ']
    lo = counts['ЛО']

    tmp_df = pd.DataFrame(data={
        'Регион': counts.index,
        'Количество поступающих': counts.values
    })

    table = dash.dash_table.DataTable(
        data=tmp_df.to_dict('records'),
        style_cell={'font_size': '20px',
                    'text_align': 'center'
                    },
    )

    return table

@callback(
    Output('regio_plot', 'figure'),
    [Input('spec_names', 'value')]
)
def update_regio_plot(spec_name):

    tmp_df = get_df_by_spec_name(df, spec_name)
    tmp_df = tmp_df[(tmp_df['regio'] != 'СПБ') & (tmp_df['regio'] != 'ЛО')]
    counts = pd.value_counts(tmp_df['regio'])
    index = counts.index[::-1]
    values = counts.values[::-1]

    tmp_df = pd.DataFrame(data={'Регион': index, 'Количество поступающих': values})

    fig = px.bar(data_frame=tmp_df, y='Регион', x='Количество поступающих', orientation='h')

    fig.update_layout(
        yaxis_title="Регион",
        xaxis_title="Количество поступающих"
    )

    return fig

@callback(
    Output('citiz_plot', 'figure'),
    [Input('spec_names', 'value')]
)
def update_citiz_plot(spec_name):
    tmp_df = get_df_by_spec_name(df, spec_name)
    tmp_df = tmp_df[tmp_df['citiz'] != 'РФ']
    counts = pd.value_counts(tmp_df['citiz'])
    index = counts.index[::-1]
    values = counts.values[::-1]

    tmp_df = pd.DataFrame(data={'Гражданство': index, 'Количество поступающих': values})

    fig = px.bar(data_frame=tmp_df, y='Гражданство', x='Количество поступающих', orientation='h')

    fig.update_layout(
        yaxis_title='Гражданство',
        xaxis_title="Количество поступающих"
    )

    return fig

@callback(
    Output('gender_plot', 'figure'),
    [Input('spec_names', 'value')]
)
def update_gender_plot(spec_name):

    tmp_df = get_df_by_spec_name(df, spec_name)

    counts = pd.value_counts(tmp_df['abGen'])
    mens = counts[1]
    womens = counts[0]

    fig = go.Figure(data=[
        go.Bar(x=['Мужчины'], y=[mens], name='Мужчины'),
        go.Bar(x=['Женщины'], y=[womens], name='Женщины')
    ]
    )

    return fig


