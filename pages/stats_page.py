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

import numpy as np

HERE = os.path.dirname(__file__)
DATA_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "stats.xlsx"))


df = pd.read_excel(DATA_FILE)

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
            dcc.Dropdown(id='edu_level', options=['Бакалавриат', 'Специалитет', 'Магистратура'], value='Бакалавриат')
        ]),
        dbc.Col(children=[
            html.H3('Форма обучения'),
            dcc.Dropdown(id='edu_form_', options=['Очное', 'Очно-заочное', 'Заочное'], value='Очное'),
        ]),
        dbc.Col(children=[
            html.H3('Форма оплаты'),
            dcc.Dropdown(id='fin_type', options=['Бюджет', 'Контракт'], value='Бюджет'),
        ])
    ])
])

mean_point = html.Div(children=[ # Блок с распределением среднего балла по специальностям
    dbc.Row(children=[
        dbc.Col(children=[
            html.H5('Направление подготовки'),
            dcc.Dropdown(id='spec_names')
        ], width=6)
    ]),
    html.Div(id='info_table'),
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
    # name_frequency,
    mean_point,
    agree_ratio,
    dop_info
])

@callback(
    Output('info_table', 'children'),
    [Input('edu_level', 'value'), Input('edu_form_', 'value'), Input('fin_type', 'value'), Input('spec_names', 'value')]
)
def get_info_table(edu_level, edu_form, fin_type, spec_name):
    tmp_df = df[(df['edu_form'] == edu_level) & (df['edu_type'] == edu_form) & (df['finance_type'] == fin_type) & (
                df['specName'] == spec_name)]

    kcp = tmp_df['kcp'].iloc[0] # Контрольные цифры
    n_z = tmp_df.shape[0] # Число заявлений
    mean_z = round(tmp_df['point_mean'].mean(), 2) # Средний балл
    mean_z_min = round(tmp_df['point_mean'].min(), 2) # Минимальный балл
    mean_z_max = round(tmp_df['point_mean'].max(), 2) # Максимальный балл

    table_dict = {
        'Контрольные цифры': [kcp],
        'Число завялений': [n_z],
        'Средний балл': [mean_z],
        'Минимальный балл': [mean_z_min],
        'Максимальный балл': [mean_z_max]
    }

    tmp_df = pd.DataFrame(table_dict)
    table = dash.dash_table.DataTable(
        data=tmp_df.to_dict('records'),
        style_cell={'font_size': '20px',
                    'text_align': 'center'
                    },
    )

    return table




@callback(
    [Output('spec_names', 'options'), Output('spec_names', 'value')],
    [Input('edu_level', 'value'), Input('edu_form_', 'value'), Input('fin_type', 'value')]
)
def get_spec_names(edu_level, edu_form, fin_type):
    tmp_df = df[(df['edu_form'] == edu_level) & (df['edu_type'] == edu_form) & (df['finance_type'] == fin_type)]

    return tmp_df['specName'].unique(), tmp_df['specName'].unique()[0]

@callback(
    Output('mean_point_plot', 'figure'),
    [Input('edu_level', 'value'), Input('edu_form_', 'value'), Input('fin_type', 'value'), Input('spec_names', 'value'),
     Input('bal_range', 'value')
     ]
)
def update_mean_point_plot(edu_level, edu_form, fin_type, spec_name, bal_range):
    tmp_df = df[(df['edu_form'] == edu_level) & (df['edu_type'] == edu_form) & (df['finance_type'] == fin_type) & (df['specName'] == spec_name)]

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
    [Input('edu_level', 'value'), Input('edu_form_', 'value'), Input('fin_type', 'value'), Input('spec_names', 'value'),
     Input('bal_range', 'value')
     ]
)
def agree_ratio(edu_level, edu_form, fin_type, spec_name, bal_range): # Отношение числа согласных к общему числу заявлений
    tmp_df = df[(df['edu_form'] == edu_level) & (df['edu_type'] == edu_form) & (df['finance_type'] == fin_type) & (df['specName'] == spec_name)]

    tmp_df = tmp_df[(tmp_df['point_mean'] > bal_range[0]) & (tmp_df['point_mean'] < bal_range[1])]

    agree = tmp_df[tmp_df['abAgr'] == 1]

    mean_z = tmp_df['point_mean'].mean()  # Средний балл заявления

    agree_mean = agree['point_mean'].mean()  # Средний балл согласия

    counts, bins = np.histogram(agree['point_mean'], bins=range(*bal_range, 2))

    bins = 0.5 * (bins[:-1] + bins[1:])

    counts = counts / tmp_df.shape[0]

    fig = px.bar(x=bins, y=counts, labels={'x': 'Средний балл', 'y': 'Отношение числа согласий к общему числу заявлений'}, height=650)

    return fig

@callback(
    Output('spb_lo', 'children'),
    [Input('spec_names', 'value')]
)
def update_spb_lo(spec_name):

    tmp_df = df[df['specName'] == spec_name]
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
    tmp_df = df[(df['specName'] == spec_name) & (df['regio'] != 'СПБ') & (df['regio'] != 'ЛО')]
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
    tmp_df = df[(df['specName'] == spec_name) & (df['citiz'] != 'РФ')]
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

    tmp_df = df[df['specName'] == spec_name]

    counts = pd.value_counts(tmp_df['abGen'])
    mens = counts[1]
    womens = counts[0]

    fig = go.Figure(data=[
        go.Bar(x=['Мужчины'], y=[mens], name='Мужчины'),
        go.Bar(x=['Женщины'], y=[womens], name='Женщины')
    ]
    )

    return fig


