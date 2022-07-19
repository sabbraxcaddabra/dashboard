import dash
import numpy as np
from dash import dcc
from dash import Input, Output, callback
from dash import html
import datetime
import pandas as pd
import time

import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import openpyxl

from getpass import getpass
from sqlalchemy import create_engine
import pymysql
import datetime

import os

from . import data_loader

DATA_LOADER = data_loader.CompareDailyLoader()
DATA_LOADER.load_data()

def get_only_needed_cols(df):

    df = df.loc[:, ['spec_code', 'add_data', 'fintype']]

    return df

def get_df_by_edu_level(df, edu_level):
    if edu_level != 'Магистратура':
        return df[df['edu_level'] != 'Магистратура']
    else:
        return df[df['edu_level'] == 'Магистратура']

def get_df_by_edu_form(tmp_df, edu_form):
    # Фильтруем по признаку Очное / Очно-Заочное / Заочное
    return tmp_df[tmp_df['edu_form'] == edu_form]

def get_df_by_fintype(tmp_df, fintype):
    if fintype != 'Бюджет (весь)':
        return tmp_df[tmp_df['fintype'] == fintype]
    return tmp_df[tmp_df['fintype'] != 'С оплатой обучения']

def get_type_dropdown_options(df):
    options = list(df['post_method'].unique())
    return ['Все'] + options

def get_df_by_date(df, date):
    date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

    df = df[df['add_data'] <= date]

    return df

def get_df_by_del_date(df, date):
    date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

    df = df[(df['add_data'] <= date) & (df['del_data'] >= date)]

    return df

def get_ok_status(df):
    return df[df['status_id'] == 2]

def filter_all(df, date, edu_level, edu_form, fintype, post_method):

    df = get_df_by_date(df, date)

    if post_method != 'Все':
        df = df[df['post_method'] == post_method]

    df = get_df_by_edu_level(df, edu_level)
    df = get_df_by_edu_form(df, edu_form)
    df = get_df_by_fintype(df, fintype)

    return df

control_elements = html.Div(children=[
    dbc.Row(children=[
        dbc.Col([
            html.Div('Выбор даты'),
            dcc.DatePickerSingle(  # Выбор промежутка дат
                id='pick_a_date_single',
                date=DATA_LOADER.data['add_data'].max(),
                max_date_allowed=DATA_LOADER.data['add_data'].max(),
                min_date_allowed=DATA_LOADER.data['add_data'].min(),
                display_format='MM-DD'
            )
        ]),
        dbc.Col(children=[
            html.Div('Уровень образования'),
            dcc.Dropdown(
                id='edu_level_dropdown',
                options=['Бакалавриат/Специалитет', 'Магистратура'],
                value='Бакалавриат/Специалитет',
                searchable=False,
                clearable=False
            )
        ]),
        dbc.Col(children=[
            html.Div('Форма обучения'),
            dcc.Dropdown(id='edu_form', options=['Очное', 'Очно-заочное', 'Заочное'], value='Очное', clearable=False),
        ]),
    ]),
])

layout = html.Div(children=[
    dcc.Interval(id='update_interval', interval=300e3),
    html.Div(id='total_compare_table', style={'marginRight': 700}),
    html.Br(),
    control_elements,
    html.Br(),
    html.Div(id='total_budget', style={'fontSize': '22px'}),
    html.Br(),
    dbc.Row(children=[
        dbc.Col(dcc.Graph(id='compare_adm_cond_osn_kontract')), # Сравнение двух лет по условиям поступления
        dbc.Col(dcc.Graph(id='compare_adm_cond_os_celo')), # Сравнение двух лет по условиям поступления
    ]),
    dbc.Row(children=[
        dbc.Col(children=[
            html.Div('Условие поступления'),
            dcc.Dropdown(
                id='type_f_dropdown',
                options=['Бюджет (весь)', 'Основные места', 'Целевая квота', 'Особая квота', 'С оплатой обучения'],
                value='Бюджет (весь)',
                searchable=False,
                clearable=False
            )
        ]),
        dbc.Col(children=[
            html.Div('Тип подачи заявления'),
            dcc.Dropdown(
                id='post_method_dropdown',
                options=get_type_dropdown_options(DATA_LOADER.data),
                value='Все',
                searchable=False,
                clearable=False
            )
        ]),
    ]),
    dcc.Graph(id='compare_adm_cond_speces'), # Сравнение двух лет на каждую специальность и по типу подачи
    dcc.Graph(id='daily_load_plot_not_cum'), # Распределение по дням
    dcc.Graph(id='daily_load_plot_cum'), # Распределение по дням кумулятивное
])


def get_counts_and_people_counts(df):
    counts = pd.value_counts(df['add_data_m_d'])
    counts = counts.sort_index()

    tmp_df = df.drop_duplicates(subset='abiturient_id')

    people_counts = pd.value_counts(tmp_df['add_data_m_d'])
    people_counts = people_counts.sort_index()

    return counts, people_counts


def get_load_scater(counts, people_counts, fig_type='not_cum'):
    locate_date = {  # Переименование месяца в дате
        '03': 'Март',
        '04': 'Апрель',
        '05': 'Май',
        '07': 'Июль',
        '06': 'Июнь'
    }

    counts = counts.sort_index()

    date = counts.index
    date_people = people_counts.index

    if fig_type == 'cum':
        values = counts.values.cumsum()
        people_values = people_counts.cumsum()
        title_text_yaxis = 'Суммарное число заявлений / людей'
    else:
        people_values = people_counts.values
        values = counts.values
        title_text_yaxis = 'Число заявлений / людей'

    new_date = []
    new_date_people = []

    for dat in date:
        new_dat = str(dat).split('-')
        new_dat[0] = locate_date[new_dat[0]]
        new_date.append('-'.join(new_dat))

    for dat in date_people:
        new_dat = str(dat).split('-')
        new_dat[0] = locate_date[new_dat[0]]
        new_date_people.append('-'.join(new_dat))

    return values, people_values, new_date, new_date_people


def get_load_figure(
        counts,
        people_counts,
        color,
        people_color,
        fig_type='not_cum'):

    values, people_values, new_date, new_date_people = get_load_scater(counts, people_counts, fig_type)
    fig = go.Figure()
    fig.add_traces(data=[
        go.Scatter(x=new_date, y=values, name='Заявления', mode='none', fill='tozeroy', fillcolor=color),
        go.Scatter(x=new_date_people, y=people_values, name='Люди', fill='tozeroy', fillcolor=people_color)
    ]
    )

    if fig_type == 'cum':
        title_text_yaxis = 'Суммарное число заявлений / людей'
    else:
        title_text_yaxis = 'Число заявлений / людей'

    fig.update_xaxes(title_text='Дата')
    fig.update_yaxes(title_text=title_text_yaxis)

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig

@callback(
    [Output('daily_load_plot_not_cum', 'figure'), Output('daily_load_plot_cum', 'figure')],
    [Input('pick_a_date_single', 'date'), Input('edu_level_dropdown', 'value'), Input('edu_form', 'value'),
     Input('type_f_dropdown', 'value'), Input('post_method_dropdown', 'value')
     ]
)
def plot_daily_load(date, edu_level, edu_form, fintype, post_method):
    df = DATA_LOADER.data
    df = filter_all(df, date, edu_level, edu_form, fintype, post_method)

    df_21 = DATA_LOADER.last_year_df
    df_21 = filter_all(df_21, date, edu_level, edu_form, fintype, post_method)
    df_21 = get_df_by_del_date(df_21, date)

    counts, people_counts = get_counts_and_people_counts(df)
    counts_21, people_counts_21 = get_counts_and_people_counts(df_21)

    total_counts = pd.DataFrame(counts).join(counts_21, rsuffix='_2021').fillna(0)
    total_people_counts = pd.DataFrame(people_counts).join(people_counts_21, rsuffix='_2021').fillna(0)

    counts = total_counts['add_data_m_d']
    people_counts = total_people_counts['add_data_m_d']

    fig = get_load_figure(counts, people_counts, '#00CC00', '#FF8500','not_cum')
    fig_cum = get_load_figure(counts, people_counts, '#0776A0', '#FF8500', 'cum')

    counts = total_counts['add_data_m_d_2021']
    people_counts = total_people_counts['add_data_m_d_2021']

    values, people_values, new_date, new_date_people = get_load_scater(counts, people_counts, fig_type='not_cum')

    fig.add_traces([
        go.Scatter(x=new_date, y=values, name='Заявления 2021', mode='lines+markers', line_color='#F23911'),
        go.Scatter(x=new_date_people, y=people_values, name='Люди 2021', mode='lines+markers')
    ])

    values, people_values, new_date, new_date_people = get_load_scater(counts, people_counts, fig_type='cum')

    fig_cum.add_traces([
        go.Scatter(x=new_date, y=values, name='Заявления 2021', mode='lines+markers', line_color='#F23911'),
        go.Scatter(x=new_date_people, y=people_values, name='Люди 2021', mode='lines+markers')
    ])


    return fig, fig_cum

def get_stats_by_year(df):

    res_dict = dict(
        n_abiturients=df.drop_duplicates('abiturient_id').shape[0],
        n_budget=df[df['fintype'] != 'С оплатой обучения'].shape[0],
        n_dou=df[df['fintype'] == 'С оплатой обучения'].shape[0],
        n_application=df.shape[0]
    )

    return res_dict

@callback(
    Output('pick_a_date_single', 'max_date_allowed'),
    [Input('update_interval', 'n_intervals')]
)
def update_dates_range(n):
    df = DATA_LOADER.data
    max_date = df['add_data'].max()
    return max_date

@callback(
    Output('total_compare_table', 'children'),
    [Input('update_interval', 'n_intervals'), Input('pick_a_date_single', 'date')]
)
def update_table(n_interval, date):
    DATA_LOADER.load_data()

    df = DATA_LOADER.data
    df = get_ok_status(df)
    df = get_df_by_date(df, date)

    df_21 = DATA_LOADER.last_year_df
    df_21 = get_df_by_del_date(df_21, date)

    print(df.shape, 'Текущий год')
    print(df_21.shape, 'Прошлый год')

    dict_22 = get_stats_by_year(df)
    dict_21 = get_stats_by_year(df_21)

    compare_df = pd.DataFrame(
        data={
            '': ['Абитуриенты, чел.', 'Бюджет, заяв.', 'ДОУ, заяв.', 'Итог, заяв.'],
            '2021': [dict_21['n_abiturients'], dict_21['n_budget'], dict_21['n_dou'], dict_21['n_application']],
            '2022': [dict_22['n_abiturients'], dict_22['n_budget'], dict_22['n_dou'], dict_22['n_application']]
        }
    )

    d_table  = dash.dash_table.DataTable(
        data=compare_df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in compare_df.columns],
        style_cell={'font_size': '20px',
                    'text_align': 'center'
                    },
    )

    return d_table

@callback(
    [Output('compare_adm_cond_osn_kontract', 'figure'),
     Output('compare_adm_cond_os_celo', 'figure'),
     Output('total_budget', 'children')
     ],
    [Input('update_interval', 'n_intervals'), Input('pick_a_date_single', 'date'), Input('edu_level_dropdown', 'value'), Input('edu_form', 'value')]
)
def plot_compare_adm_plot(n_intervals, date, edu_level, edu_form):

    df = DATA_LOADER.data
    df = get_ok_status(df)
    df = get_df_by_date(df, date)
    df = get_df_by_edu_level(df, edu_level)
    df = get_df_by_edu_form(df, edu_form)

    df_21 = DATA_LOADER.last_year_df
    df_21 = get_df_by_del_date(df_21, date)
    df_21 = get_df_by_edu_level(df_21, edu_level)
    df_21 = get_df_by_edu_form(df_21, edu_form)

    df = get_only_needed_cols(df)
    df_21 = get_only_needed_cols(df_21)

    df['Год'] = 2022
    df_21['Год'] = 2021

    total_df = pd.concat((df, df_21), ignore_index=True)


    counts = pd.value_counts(df['fintype'])
    counts_21 = pd.value_counts(df_21['fintype'])

    os_and_celo = total_df[(total_df['fintype'] == 'Особая квота') | (total_df['fintype'] == 'Целевая квота')]
    osn_and_kontract = total_df[(total_df['fintype'] == 'Основные места') | (total_df['fintype'] == 'С оплатой обучения')]

    fig_os_and_celo = px.histogram(os_and_celo, x='fintype', color='Год', barmode='group', text_auto=True)
    fig_osn_and_kontract = px.histogram(osn_and_kontract, x='fintype', color='Год', barmode='group', text_auto=True)

    fig_osn_and_kontract.update_traces(textposition='outside')
    fig_os_and_celo.update_traces(textposition='outside')

    max_os_celo = pd.value_counts(os_and_celo['fintype']).max()
    max_osn_kontract = pd.value_counts(osn_and_kontract['fintype']).max()

    fig_osn_and_kontract.update_layout(
        xaxis_title="Тип финансирования",
        yaxis_title="Кол-во заявлений",
        font=dict(
            size=18
        )
    )


    fig_os_and_celo.update_layout(
        xaxis_title="Тип финансирования",
        yaxis_title="Кол-во заявлений",
        font=dict(
            size=18,
        )
    )

    fig_osn_and_kontract.update_yaxes(range=[0, max_osn_kontract * 1.2])
    fig_os_and_celo.update_yaxes(range=[0, max_os_celo * 1.2])

    div_text = f'Всего заявлений на бюджет (21/22): {df_21[df_21["fintype"] != "С оплатой обучения"].shape[0]}/{df[df["fintype"] != "С оплатой обучения"].shape[0]}'

    return fig_osn_and_kontract, fig_os_and_celo, div_text


@callback(
    Output('compare_adm_cond_speces', 'figure'),
    [Input('pick_a_date_single', 'date'), Input('edu_level_dropdown', 'value'), Input('edu_form', 'value'),
     Input('type_f_dropdown', 'value'), Input('post_method_dropdown', 'value')
     ]
)
def plot_compare_adm_plot(date, edu_level, edu_form, fintype, post_method):


    df = DATA_LOADER.data
    df = get_ok_status(df)
    df = filter_all(df, date, edu_level, edu_form, fintype, post_method)

    df_21 = DATA_LOADER.last_year_df
    df_21 = filter_all(df_21, date, edu_level, edu_form, fintype, post_method)
    df_21 = get_df_by_del_date(df_21, date)

    df = get_only_needed_cols(df)
    df_21 = get_only_needed_cols(df_21)

    df['Год'] = 2022
    df_21['Год'] = 2021

    total_df = pd.concat((df, df_21), ignore_index=True)
    fig = px.histogram(total_df, x='spec_code', color='Год', barmode='group').update_xaxes(categoryorder='total ascending')

    fig.update_layout(
        xaxis_title="Код направления подготовки",
        yaxis_title="Кол-во заявлений"
    )

    return fig


