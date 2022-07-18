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
import openpyxl

from getpass import getpass
from sqlalchemy import create_engine
import pymysql
import datetime

import os

from . import data_loader

DATA_LOADER = data_loader.CompareDailyLoader()
DATA_LOADER.load_data()

def get_df_by_edu_level(df, edu_level):
    if edu_level != 'Магистратура':
        return df[df['edu_form'] != 'Магистратура']
    else:
        return df[df['edu_form'] == 'Магистратура']

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
                id='pick_a_date',
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
    control_elements,
    dcc.Graph(id='compare_adm_cond'), # Сравнение двух лет по условиям поступления
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

def get_load_figure(
        counts,
        people_counts,
        color,
        people_color,
        fig_type='not_cum'):

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


    fig = go.Figure()
    fig.add_traces(data=[
        go.Scatter(x=new_date, y=values, name='Заявления', mode='none', fill='tozeroy', fillcolor=color),
        go.Scatter(x=new_date_people, y=people_values, name='Люди', fill='tozeroy', fillcolor=people_color)
    ]
    )
    fig.update_xaxes(title_text='Дата')
    fig.update_yaxes(title_text=title_text_yaxis)

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig

@callback(
    [Output('daily_load_plot_not_cum', 'figure'), Output('daily_load_plot_cum', 'figure')],
    [Input('pick_a_date', 'date'), Input('edu_level_dropdown', 'value'), Input('edu_form', 'value'),
     Input('type_f_dropdown', 'value'), Input('post_method_dropdown', 'value')
     ]
)
def plot_daily_load(date, edu_level, edu_form, fintype, post_method):
    df = DATA_LOADER.data
    df = filter_all(df, date, edu_level, edu_form, fintype, post_method)

    counts, people_counts = get_counts_and_people_counts(df)

    fig = get_load_figure(counts, people_counts, '#00CC00', '#FF8500','not_cum')
    fig_cum = get_load_figure(counts, people_counts, '#0776A0', '#FF8500', 'cum')

    return fig, fig_cum

@callback(
    Output('compare_adm_cond', 'figure'),
    [Input('pick_a_date', 'date'), Input('edu_level_dropdown', 'value'), Input('edu_form', 'value')]
)
def plot_compare_adm_plot(date, edu_level, edu_form):


    df = DATA_LOADER.data
    df = get_df_by_date(df, date)
    df = get_df_by_edu_level(df, edu_level)
    df = get_df_by_edu_form(df, edu_form)

    counts = pd.value_counts(df['fintype'])


    fig = go.Figure()
    fig.add_trace(go.Bar(name="Основные места", x=["2022"], y=[counts.get("Основные места", 0)]))
    fig.add_trace(go.Bar(name="С оплатой обучения", x=["2022"], y=[counts.get("С оплатой обучения", 0)]))
    fig.add_trace(go.Bar(name="Целевая квота", x=["2022"], y=[counts.get("Целевая квота", 0)]))
    fig.add_trace(go.Bar(name="Целевая квота", x=["2022"], y=[counts.get("Целевая квота", 0)]))
    fig.update_layout(barmode='group')

    fig.update_layout(
        xaxis_title="Тип финансирования",
        yaxis_title="Кол-во заявлений"
    )

    return fig

@callback(
    Output('compare_adm_cond_speces', 'figure'),
    [Input('pick_a_date', 'date'), Input('edu_level_dropdown', 'value'), Input('edu_form', 'value'),
     Input('type_f_dropdown', 'value'), Input('post_method_dropdown', 'value')
     ]
)
def plot_compare_adm_plot(date, edu_level, edu_form, fintype, post_method):


    df = DATA_LOADER.data
    df = filter_all(df, date, edu_level, edu_form, fintype, post_method)

    fig = px.histogram(df, x='spec_code').update_xaxes(categoryorder='total ascending')

    fig.update_layout(
        xaxis_title="Код направления подготовки",
        yaxis_title="Кол-во заявлений"
    )

    return fig

