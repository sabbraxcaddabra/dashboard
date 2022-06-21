from getpass import getpass
from sqlalchemy import create_engine
import pymysql
import pandas as pd
import datetime


query = """
    SELECT 
    application.abiturient_id AS abiturient_id,
    specialty.id AS spec_id,
    specialty.name AS spec_name,
    specialty.code AS spec_code,
    specialty.level_id AS edu_level_id,
    edulevel.name AS edu_level,
    application.fintype_id AS fintype_id,
    fintype.name AS fintype,
    application.eduform_id AS edu_form_id,
    eduform.name AS edu_form,
    side_info.post_method_id AS post_method_id,
    post_method.name AS post_method,
    application.add_time AS add_data,
    edu_doc.original AS original,
    fd.name AS disc_1,
    fae.points AS disc_point_1,
    sd.name AS disc_2,
    sae.points AS disc_point_2,
    td.name AS disc_3,
    tae.points AS discpoint_3,
    (fae.points + sae.points + tae.points) AS sum_point
    FROM
    application
        LEFT JOIN
    specialty ON specialty.id = application.specialty_id
        LEFT JOIN
    fintype ON fintype.id = application.fintype_id
        LEFT JOIN
    eduform ON eduform.id = application.eduform_id
        LEFT JOIN
    side_info ON side_info.abiturient_id = application.abiturient_id
        LEFT JOIN
    post_method ON post_method.id = side_info.post_method_id
        LEFT JOIN
    edu_doc ON edu_doc.abiturient_id = application.abiturient_id
        LEFT JOIN
    edulevel ON edulevel.id = specialty.level_id
        LEFT JOIN
    admission_direction AS fda ON fda.specialty_id = specialty.id
        LEFT JOIN
    admission_direction_exam_slot AS fades ON fades.admission_direction_id = fda.id
        AND fades.priority = 1
        LEFT JOIN
    admission_direction_exam AS fade ON fade.slot_id = fades.id
        LEFT JOIN
    admission_direction AS sda ON sda.specialty_id = specialty.id
        LEFT JOIN
    admission_direction_exam_slot AS sades ON sades.admission_direction_id = sda.id
        AND sades.priority = 2
        LEFT JOIN
    admission_direction_exam AS sade ON sade.slot_id = sades.id
        LEFT JOIN
    admission_direction AS tda ON tda.specialty_id = specialty.id
        LEFT JOIN
    admission_direction_exam_slot AS tades ON tades.admission_direction_id = tda.id
        AND tades.priority = 3
        LEFT JOIN
    admission_direction_exam AS tade ON tade.slot_id = tades.id
        LEFT JOIN
    abiturient_exam AS fae ON fae.discipline_id = fade.discipline_id
        AND fae.abiturient_id = application.abiturient_id
        LEFT JOIN
    discipline AS fd ON fd.id = fae.discipline_id
        LEFT JOIN
    abiturient_exam AS sae ON sae.discipline_id = sade.discipline_id
        AND sae.abiturient_id = application.abiturient_id
        LEFT JOIN
    discipline AS sd ON sd.id = sae.discipline_id
        LEFT JOIN
    abiturient_exam AS tae ON tae.discipline_id = tade.discipline_id
        AND tae.abiturient_id = application.abiturient_id
        LEFT JOIN
    discipline AS td ON td.id = tae.discipline_id
    WHERE
    fda.campaign_id <> 3
        AND sda.campaign_id <> 3
        AND tda.campaign_id <> 3
        AND fae.points <> 0
        AND sae.points <> 0
        AND tae.points <> 0
        """

engine = create_engine(
    'mysql+pymysql://c3h6o:2m9fpHFVa*Z*UF@172.24.129.190/arm2022'
)

connection = engine.connect()
df = pd.read_sql(query, connection, parse_dates={'add_data': '%y/%m/%d'})
df['add_data'] = df['add_data'].dt.date


# def count_orig(series):
#     counts = pd.value_counts(series).get(1, 0)
#     return counts

# today = datetime.date.today()

# today_df = df[df['add_data'] == today]


# grouped = today_df.groupby(['spec_code', 'spec_name', 'edu_form']).agg({'spec_name': 'count', 'original': count_orig})

# grouped = grouped.rename(columns={'spec_name': 'Заявлений', 'original': 'Оригиналов'})
# print(grouped)