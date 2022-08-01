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

DATA_LOADER = data_loader.DailyDataLoader()
DATA_LOADER.load_data()

HERE = os.path.dirname(__file__)

def autofit_columns(filepath):

    wb = openpyxl.load_workbook(filepath)
    sheet = wb['Sheet1']

    dims = {}

    rows = list(sheet.rows)
    for row in rows:
        for cell in row:
            if cell.value:
                dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), len(str(cell.value)) * 1.5))

    for col, value in dims.items():
        sheet.column_dimensions[col].width = value

    wb.save(filepath)

def get_budget(series):
    tmp_series = series[series != 'С оплатой обучения']
    return tmp_series.shape[0]

def get_contract(series):
    tmp_series = series[series == 'С оплатой обучения']
    return tmp_series.shape[0]

def count_orig(series):
    counts = pd.value_counts(series).get(1, 0)
    return counts

def get_total_stats(df):
    grouped = df.groupby('edu_form').agg(
        spec_name_count=('spec_name', lambda series: series.shape[0]),
        # people_count=('abiturient_id', 'nunique'),
        original_count=('orig_and_agree', count_orig),
        budget=('fintype', get_budget),
        kontract=('fintype', get_contract)
    )
    grouped = grouped.reset_index()
    grouped.insert(loc=0, column='spec_code', value='-')
    grouped.insert(loc=1, column='spec_name', value='Итого')
    if grouped.shape[0] > 2:
        och, z = grouped.iloc[0], grouped.iloc[2]
        grouped.iloc[0], grouped.iloc[2] = z, och

    return grouped

def day_stats(df):
    grouped = df.groupby(['spec_code', 'spec_name', 'edu_form']).agg(
        spec_name_count=('spec_name', 'count'),
        # people_count=('abiturient_id', 'nunique'),
        original_count=('orig_and_agree', count_orig),
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
    sorted_df = grouped.sort_values(by=['edu_level_code_num', 'spec_code'], ascending=True)
    del sorted_df['edu_level_code_num']
    return sorted_df

def get_ok_status(df):
    return df[df['status_id'] == 2]

def get_stats(df):
    df = get_ok_status(df)
    grouped = day_stats(df)
    df_table = sort_by_edu_level(grouped)
    total = get_total_stats(df)
    df_table = pd.concat((total, df_table), ignore_index=True)
    df_table = df_table.rename(columns={
        'spec_code': 'Код',
        'spec_name': 'Название',
        'edu_form': 'Форма обучения',
        'budget': 'Заявлений на бюджет',
        'kontract': 'Заявлений на контракт',
        'spec_name_count': 'Заявлений всего',
        'original_count': 'Оригиналов',
        # 'people_count': 'Людей'
        }
    )
    return df_table


def get_today_table(df):
    today = datetime.date.today()
    today_df = df[df['add_data'] == today]
    df_table = get_stats(today_df)
    d_table  = dash.dash_table.DataTable(
        data=df_table.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_table.columns],
        style_cell={
                    'text_align': 'left'
                    },
        style_cell_conditional=[
            {
                'if': {'column_id': 'spec_name'},
                'textAlign': 'left'
            }
        ]
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

def get_type_dropdown_options(df):
    options = list(df['post_method'].unique())
    return ['Все'] + options

def get_min_data():
    df = DATA_LOADER.data
    min_data = df['add_data'].min()
    min_data = datetime.datetime.strptime(min_data, 'yyyy-mm-dd')
    return min_data

def get_max_data():
    df = DATA_LOADER.data
    min_data = df['add_data'].max()
    min_data = datetime.datetime.strptime(min_data, 'yyyy-mm-dd')
    return min_data

def get_status_z(df):  # Отрисовывает график со статусами заявлений

    df = df.drop_duplicates(subset=['abiturient_id'])

    df.to_excel('status.xlsx')

    fig = px.histogram(data_frame=df, x='status_name', color='status_name')
    fig.update_layout(legend_title_text='Статус заявления')

    fig.update_layout(
        yaxis_title="Количество",
        xaxis_title="Тип статуса"
    )

    return fig

daily_load = html.Div(children=[
    dcc.Interval(id='date_range_update', interval=86.4e6),
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
    html.Div('Сводка на сегодня (* учитываются только заявления в статусе проверено)'),
    html.Br(),
    dbc.Row(children=[
        dbc.Col(children=[
            html.Button(id='today_report_button', children='Сформировать отчет за сегодня в Excel')
        ], width=4),
        dbc.Col(children=[
            html.Button(id='total_report_button', children='Сформировать отчет за все время в Excel'),
        ], width=4),
    ]),
    html.Br(),
    html.Div(id='daily_table'),
    html.Br(),
    # dcc.Graph(figure=get_today_table(), id='today_table'),
    dbc.Row(children=[  # Строчка с распределением нагрузки по дням и типу подачи заявления
        dbc.Col([
            html.Div('Период дней'),
            dcc.DatePickerRange(  # Выбор промежутка дат
                id='pick_a_date',
                start_date=DATA_LOADER.data['add_data'].min(),
                end_date=DATA_LOADER.data['add_data'].max(),
                max_date_allowed=DATA_LOADER.data['add_data'].max(),
                min_date_allowed=DATA_LOADER.data['add_data'].min(),
                display_format='Y-MM-DD'
            )
        ]),
        dbc.Col(children=[
            html.Div('Уровень образования'),
            dcc.Dropdown(
                id='edu_level_dropdown',
                options=['Все', 'Бакалавриат', 'Специалитет', 'Магистратура'],
                value='Все',
                searchable=False,
                clearable=False
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
                options=get_type_dropdown_options(DATA_LOADER.data),
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
    dcc.Graph(figure=get_status_z(DATA_LOADER.data), id='status_z_plot')
])

status_pz = html.Div(children=[  # Блок с графиком статусов абитуриента
    html.H2('Статус абитуриента'),
    dbc.Row(children=[status_z])
])

check_needed = html.Div(children=[
    # dcc.Download(id='check_needed'),
    dcc.Download(id='check_ind_needed'),
    dcc.Download(id='check_id_last_changes'),
    dcc.Download(id='check_id_not_orig_or_agree'),
    dcc.Download(id='check_os_pravo'),
    dcc.Download(id='check_id_not_epgu'),
    dcc.Download(id='check_epgu_snils'),
    dcc.Download(id='check_epgu_inoe'),
    dcc.Download(id='check_epgu_id_otl'),
    dcc.Download(id='check_epgu_script'),
    dbc.DropdownMenu(
        label='Выберите тип выгрузки',
        children=[
            dbc.DropdownMenuItem('Проверка ИД', id='check_ind_needed_button'),
            dbc.DropdownMenuItem('Проверка особого права', id='check_os_pravo_button'),
            dbc.DropdownMenuItem('Проверка Последнее изменение ЛК', id='check_id_last_change_button'),
            dbc.DropdownMenuItem('Проверка дел с согласием без оригинала / оригиналом без согласия', id='check_id_not_orig_or_agree_button'),
            dbc.DropdownMenuItem('Требует проверки не ЕПГУ', id='check_id_not_epgu_button'),
            dbc.DropdownMenuItem('Проверка с ЕПГУ со СНИЛС', id='check_epgu_snils_button'),
            dbc.DropdownMenuItem('Образование "Иное ЕПГУ"', id='check_epgu_inoe_button'),
            dbc.DropdownMenuItem('Проверка ЕПГУ ИД "С отличием"', id='check_epgu_id_otl_button'),
            dbc.DropdownMenuItem('Последние изменения СКРИПТ ЕПГУ', id='check_epgu_script_button'),
        ],
        size="lg",
        direction='end'
    ),
    # dbc.Row(children=[
    #     # dbc.Col(children=[html.Button('Выгрузить номера дел требующих проверки', id='check_needed_button')], width=3),
    #     dbc.Col(children=[html.Button('Выгрузить номера дел с особым правом(олимпиады)', id='check_os_pravo_button')]),
    #     dbc.Col(children=[html.Button('Выгрузить номера дел требующих проверки ИД', id='check_ind_needed_button')]),
    # ]),
    # html.Br(),
    # dbc.Row(children=[
    #     # dbc.Col(children=[html.Button('Выгрузить номера дел с особым правом(олимпиады)', id='check_os_pravo_button')], width=3),
    #     dbc.Col(children=[html.Button('Выгрузить номера дел с последним изменением в ЛК', id='check_id_last_change_button')]),
    #     dbc.Col(children=[html.Button('Выгрузить номера дел с согласием без оригинала / оригиналом без согласия', id='check_id_not_orig_or_agree_button')]),
    # ])
])

layout = html.Div(children=[
    html.H2('Распределение нагрузки по дням'),
    daily_load,
    html.Br(),
    html.Div(id='hostel_needed', style={'fontSize': 22}),
    html.Br(),
    check_needed,
    html.Br(),
    status_pz
])

def get_df_by_edu_level(tmp_df, edu_level):
    # Фильтруем по признаку Бакалавриат / Специалитет / Магистратура
    return tmp_df[tmp_df['edu_level'] == edu_level]

def update_dates(df):
    return df['add_data'].min(), df['add_data'].max()

def get_df_by_fintype(tmp_df, fintype):
    # Фильтруем по признаку Бюджет / Контракт
    if fintype != 'Контракт':
        return tmp_df[tmp_df['fintype'] != 'С оплатой обучения']
    else:
        return tmp_df[tmp_df['fintype'] == 'С оплатой обучения']

def get_df_by_app_type(df, app_type):
    if app_type == 'Заявление с согласием':
        df = df[df['agree'] == 1]
    elif app_type =='Заявление с оригиналом':
        df = df[df['original'] == 1]

    return df

@callback(
    Output('check_epgu_script', 'data'),
    [Input('check_epgu_script_button', 'n_clicks')], prevent_initial_call=True
)
def check_epgu_script(n_clicks):
    query = '''
    select  ab.id, if((select count(id) from application where abiturient_id = ab.id and deleted_at is null) > 0, 1, 0) as apps
    from abiturient as ab
    where (select user_id from check_record where abiturient_id = ab.id order by created_at desc limit 0, 1) = 54 and ab.status_id not in (1, 2, 4) and ab.id not in
    (select abiturient_id from abiturient_lock)
    '''

    df = DATA_LOADER.get_check_by_query(query)
    return dcc.send_data_frame(df.to_excel, "Последнее изменение СКРИПТ ЕПГУ.xlsx", sheet_name="Sheet_name_1")


@callback(
    Output('check_epgu_id_otl', 'data'),
    [Input('check_epgu_id_otl_button', 'n_clicks')], prevent_initial_call=True
)
def check_epgu_id_otl(n_clicks):
    query = '''
        select
      abiturient.id
    from
      abiturient join side_info on side_info.abiturient_id = abiturient.id
    where
      side_info.post_method_id = 3 and abiturient.status_id != 1 and abiturient.id in (select ach.abiturient_id from achievement as ach join abiturient as ab on ab.id = ach.abiturient_id
        where ach.deleted_at is null and ach.type_id in (6, 7, 20)
        and (select concat(user_id, ' ', 1) from check_record where abiturient_id = ab.id and record_type = 'achievement' and ach.id = record_id order by created_at desc limit 0, 1) like '%% 1')
    '''

    df = DATA_LOADER.get_check_by_query(query)
    return dcc.send_data_frame(df.to_excel, "ЕПГУ ИД  'С отличием'.xlsx", sheet_name="Sheet_name_1")

@callback(
    Output('check_epgu_inoe', 'data'),
    [Input('check_epgu_inoe_button', 'n_clicks')], prevent_initial_call=True
)
def check_epgu_inoe(n_clicks):
    query = '''
        select
      edu_doc.abiturient_id
    from
      edu_doc join abiturient on abiturient.id = edu_doc.abiturient_id join side_info on side_info.abiturient_id = abiturient.id
    where
      abiturient.status_id = 2 and edu_doc.deleted_at is null and edu_doc.type_id = 10 and side_info.post_method_id = 3
    '''

    df = DATA_LOADER.get_check_by_query(query)
    return dcc.send_data_frame(df.to_excel, "ЕГПУ_иное.xlsx", sheet_name="Sheet_name_1")

@callback(
    Output('check_epgu_snils', 'data'),
    [Input('check_epgu_snils_button', 'n_clicks')], prevent_initial_call=True
)
def check_epgu_snils(n_clicks):
    query = '''
        select
       right(abiturient.id, if(abiturient.id >= 202210000, 5, 4)) as num, (select max(created_at) from check_record where abiturient_id = abiturient.id) as last
         , if((select count(points) from abiturient_exam where abiturient_id = abiturient.id and deleted_at is null) > 0, 1, 0) as ex
    from
      abiturient join side_info on side_info.abiturient_id = abiturient.id
    where
      abiturient.status_id = 3 and side_info.post_method_id = 3 and abiturient.id in (select abiturient_id from application where application.deleted_at is null)
        and abiturient.id not in (select abiturient_id from abiturient_lock) and side_info.snils is not null
    order by ex desc;
    '''

    df = DATA_LOADER.get_check_by_query(query)
    return dcc.send_data_frame(df.to_excel, "ЕГПУ_со_снилс.xlsx", sheet_name="Sheet_name_1")

@callback(
    Output('check_id_not_epgu', 'data'),
    [Input('check_id_not_epgu_button', 'n_clicks')], prevent_initial_call=True
)
def check_not_epgu(n_clicks):
    query = '''
    select ab.id from abiturient as ab join side_info on side_info.abiturient_id = ab.id
    where ab.id not in (select abiturient_lock.abiturient_id from abiturient_lock where user_id in (6, 54, 71, 72, 73)) and (ab.status_id in (3, 4)
    and if((select user_id from check_record where abiturient_id = ab.id order by created_at desc limit 0, 1) = 6, true, false)
    or (ab.status_id = 3 and side_info.post_method_id != 3)) and ab.id in (select abiturient_id from application where deleted_at is null) order by ab.id;
    '''

    df = DATA_LOADER.get_check_by_query(query)
    return dcc.send_data_frame(df.to_excel, "Для_проверки_не_ЕГПУ.xlsx", sheet_name="Sheet_name_1")

@callback(
    Output('check_os_pravo', 'data'),
    [Input('check_os_pravo_button', 'n_clicks')], prevent_initial_call=True
)
def check_os_pravo(n_clicks):
    query = '''
        select
     abiturient.id as 'Номер дела'
    from
     abiturient
    where abiturient.id in (select abiturient_id from olymp where deleted_at is null);
    '''
    #
    # connection = engine.connect()
    # df = pd.read_sql(query, connection)
    # connection.close()


    df = DATA_LOADER.get_check_by_query(query)
    return dcc.send_data_frame(df.to_excel, "Для_проверки_Особого_права.xlsx", sheet_name="Sheet_name_1")

@callback(
    Output('check_ind_needed', 'data'),
    [Input('check_ind_needed_button', 'n_clicks')], prevent_initial_call=True
)
def check_ind_d(n_clicks):
    # engine = create_engine(
    #         'mysql+pymysql://c3h6o:2m9fpHFVa*Z*UF@172.24.129.190/arm2022'
    #     )

    query = '''
    select
      abiturient.id
    from 
      abiturient
    where
      abiturient.status_id = 2 and abiturient.id in 
        (select achievement.abiturient_id from achievement where achievement.deleted_at is null and achievement.value = 0);
    '''

    df = DATA_LOADER.get_check_by_query(query)

    # connection = engine.connect()
    # df = pd.read_sql(query, connection)
    # connection.close()
    return dcc.send_data_frame(df.to_excel, "Для_проверки_ИД.xlsx", sheet_name="Sheet_name_1")

@callback(
    Output('check_id_not_orig_or_agree', 'data'),
    [Input('check_id_not_orig_or_agree_button', 'n_clicks')], prevent_initial_call=True
)
def check_id_not_orig_or_agree(n_clicks):
    query = '''
        select
      allo.abid as 'Номер дела',
        allo.orig as 'Оригинал',
        allo.sogl as 'Согласие'
        from (select
      ab.id as abId,
      if(ab.id in (select abiturient_id from edu_doc where deleted_at is null and original = 1), 1, 0) as orig,
        ifnull((select specialty.name from consent join application on application.id = consent.application_id 
        join specialty on specialty.id = application.specialty_id where consent.deleted_at is null and consent.abiturient_id = ab.id and application.fintype_id not in (2, 4)), '-') as sogl,
     ifnull((select specialty.name from consent join application on application.id = consent.application_id 
      join specialty on specialty.id = application.specialty_id where consent.deleted_at is null and consent.abiturient_id = ab.id and application.fintype_id in (2, 4)), '-') as soglP
    from
      abiturient as ab) as allo
    where
      (allo.orig != 1 and allo.sogl != '-' and allo.soglP = '-') or (allo.orig = 1 and allo.sogl = '-' and allo.soglP = '-');
    '''

    df = DATA_LOADER.get_check_by_query(query)
    return dcc.send_data_frame(df.to_excel, "Номера дел с согласием без оригинала / оригиналом без согласия.xlsx", sheet_name="Sheet_name_1")


@callback(
    Output('check_id_last_changes', 'data'),
    [Input('check_id_last_change_button', 'n_clicks')], prevent_initial_call=True
)
def check_id_last_change(n_clicks):

    query = '''
        select
      ab.id
    from 
      abiturient as ab
    where
      ab.id not in (select abiturient_lock.abiturient_id from abiturient_lock where user_id = 6)
      and if((select created_at from abiturient_progress where abiturient_id = ab.id and user_id = 6 order by created_at desc limit 0, 1) > 
        (select created_at from check_record where abiturient_id = ab.id and user_id != 6 order by created_at desc limit 0, 1), true, false);
    '''
    df = DATA_LOADER.get_check_by_query(query)
    return dcc.send_data_frame(df.to_excel, "Последнее_изменение_ЛК.xlsx", sheet_name="Sheet_name_1")



@callback(
    Output('check_needed', 'data'),
    [Input('check_needed_button', 'n_clicks')], prevent_initial_call=True
)
def check_arm(n_clicks):

    query = '''
    select
      ab.id
    from 
      abiturient as ab
    where
      ab.status_id = 4 and ab.id not in (select abiturient_lock.abiturient_id from abiturient_lock where user_id = 6)
      and if((select created_at from abiturient_progress where abiturient_id = ab.id and user_id = 6 order by created_at desc limit 0, 1) > 
        (select created_at from check_record where abiturient_id = ab.id and user_id != 6 order by created_at desc limit 0, 1), true, false)
    '''

    df = DATA_LOADER.get_check_by_query(query)
    return dcc.send_data_frame(df.to_excel, "Для_проверки_АРМ.xlsx", sheet_name="Sheet_name_1")

@callback(
    [Output('pick_a_date', 'start_date'), Output('pick_a_date', 'end_date'), Output('pick_a_date', 'max_date_allowed'),
    Output('pick_a_date', 'min_date_allowed')],
    [Input('date_range_update', 'n_intervals')]
)
def update_dates_range(n):
    min_date, max_date = update_dates(DATA_LOADER.data)
    return min_date, max_date, max_date, min_date

def get_hostel_num(df):
    tmp_df = df.drop_duplicates(subset='abiturient_id')
    counts = pd.value_counts(tmp_df['hostel']).get(1, 0)
    return f'Общежитие требуется: {counts} человек'

@callback(
    [Output('load_date', 'children'), Output('status_z_plot', 'figure'), Output('daily_table', 'children'),
     Output('type_dropdown', 'options'), Output('hostel_needed', 'children')
     ],
    [Input('load_date_interval', 'n_intervals')]
)
def update_data(n):
    DATA_LOADER.load_data()
    date = datetime.datetime.strftime(DATA_LOADER.load_date, '%Y-%m-%d %H:%M')
    return date, get_status_z(DATA_LOADER.data), get_today_table(DATA_LOADER.data),\
           get_type_dropdown_options(DATA_LOADER.data), get_hostel_num(DATA_LOADER.data)

def get_load_figure(counts, people_counts, color, people_color, fig_type='not_cum'):

    locate_date = {  # Переименование месяца в дате
        '03': 'Март',
        '04': 'Апрель',
        '05': 'Май',
        '07': 'Июль',
        '06': 'Июнь',
        '08': 'Август',
        '09': 'Сентябрь',
        '10': 'Октябрь',
        '11': 'Ноябрь',
        '12': 'Декабрь',

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
        new_dat[1] = locate_date[new_dat[1]]
        new_date.append('-'.join(new_dat))

    for dat in date_people:
        new_dat = str(dat).split('-')
        new_dat[1] = locate_date[new_dat[1]]
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
    [Output('daily_load_plot', 'figure'), Output('daily_load_cum_plot', 'figure')],
    [Input("load_date_interval", 'n_intervals'), Input("pick_a_date", "start_date"), Input("pick_a_date", "end_date"),
     Input('type_dropdown', 'value'), Input('type_z_dropdown', 'value'), Input('type_f_dropdown', 'value'), Input('edu_level_dropdown', 'value')]
)
def plot_daily_load(n, start, end, post_type, app_type, fintype, edu_level):
    '''
    Функция отрисовывает график нагрузки по дням
    :param start: Начало периода
    :param end: Конец периода
    :param type: Тип подачи заявления
    :return: график типа area
    '''
    start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
    end = datetime.datetime.strptime(end, '%Y-%m-%d').date()

    df = DATA_LOADER.load_data()
    if fintype != 'Все':
        df = get_df_by_fintype(df, fintype)
    if app_type != 'Все':
        df = get_df_by_app_type(df, app_type)
    if edu_level != 'Все':
        df = get_df_by_edu_level(df, edu_level)

    above = df['add_data'] >= start
    below = df['add_data'] <= end

    tmp_df = df.loc[above & below]
    
    if post_type != 'Все':
        tmp_df = tmp_df[tmp_df['post_method'] == post_type]

    counts = pd.value_counts(tmp_df['add_data'])
    counts = counts.sort_index()

    tmp_df = tmp_df.drop_duplicates(subset='abiturient_id')

    people_counts = pd.value_counts(tmp_df['add_data'])
    people_counts = people_counts.sort_index()

    fig = get_load_figure(counts, people_counts, 'rgba(43, 123, 231, 0.6)', 'rgba(241, 50, 31, 0.6)', 'not_cum')
    fig_cum = get_load_figure(counts, people_counts, 'rgba(43, 123, 231, 0.6)', 'rgba(241, 50, 31, 0.6)', 'cum')

    return fig, fig_cum


@callback(
    Output('today_report', 'data'),
    [Input('today_report_button', "n_clicks")], prevent_initial_call=True
)
def download_today(n_clics):
    today = datetime.date.today()
    df = DATA_LOADER.data
    today_df = df[df['add_data'] == today]
    df_table = get_stats(today_df)
    df_table.to_excel(f'{today}.xlsx', index=False)
    report_file = os.path.abspath(os.path.join(HERE, "..", f'{today}.xlsx'))
    autofit_columns(f'{today}.xlsx')
    return dcc.send_file(f'{today}.xlsx')

@callback(
    Output('total_report', 'data'),
    [Input('total_report_button', 'n_clicks')], prevent_initial_call=True
)
def download_total(n_clics):
    today = datetime.date.today()
    df = DATA_LOADER.data
    df_table = get_stats(df)
    df_table.to_excel(f'{today}_total.xlsx', index=False)
    report_file = os.path.abspath(os.path.join(HERE, "..", f'{today}_total.xlsx'))
    autofit_columns(f'{today}_total.xlsx')
    # autofit_columns(report_file)
    return dcc.send_file(f'{today}_total.xlsx')
