import pandas as pd
from sqlalchemy import create_engine
import pymysql
import datetime

import os
import json

HERE = os.path.dirname(__file__)
TOTAL_KCP_FILE = os.path.abspath(os.path.join(HERE, "..", "data", "../data/total_kcp.json"))
LAST_YEAR_DATA = os.path.abspath(os.path.join(HERE, ".", "srez21.xlsx"))


def get_engine():
    CONFIG_FILE = os.path.abspath(os.path.join(HERE, "..", "config.json"))

    with open(CONFIG_FILE, encoding='utf-8') as config_file:
        config_dict = json.load(config_file)
        db_config = config_dict['db_config']
        username = db_config['username']
        password = db_config['password']
        host = db_config['host']
        db_name = db_config['db_name']
        
    try:
        engine = create_engine(
            f'mysql+pymysql://{username}:{password}@{host}/{db_name}'
        )
        conn = engine.connect()
        conn.close()
    except:
        engine = create_engine(
            'mysql+pymysql://root:1999007vm@localhost/arm2022'
        )
        conn = engine.connect()
        conn.close()

    return engine




class DailyDataLoader:
    _data = None
    _load_date = None
    _engine = get_engine()

    _query = """
        select
          base.ss_agr, base.app_id, base.abId as 'abiturient_id', base.statId as 'status_id', base.statN as 'status_name', base.hos as 'hostel', base.specId as 'spec_id', base.specN as 'spec_name', base.specC as 'spec_code', 
            base.specP as 'profile_name', base.eduId as 'edu_level_id', base.eduN as 'edu_level', base.finId as 'fintype_id', base.finN as 'fintype', base.forId as 'edu_from_id', 
            base.forN as 'edu_form', base.posId as 'post_method_id', base.posN as 'post_method', base.tim as 'add_data', base.org as 'original', base.agr as 'agree', base.dog as 'dogovor',
            base.decNum as 'decree_num', base.decData as 'dec_data'
        from 
        (select
            consent.sspriem_mark as ss_agr, application.id as app_id, abiturient.id as abId, abiturient_status.id as statId, abiturient_status.name as statN, side_info.hostel as hos, specialty.id as specId, specialty.name as specN, specialty.code as specC, 
                specialty_profile.name as specP, edulevel.id as eduId, edulevel.name as eduN, fintype.id as finId, fintype.name as finN, eduform.id as forId, eduform.name as forN, post_method.id as posId, post_method.name as posN, application.add_time as tim,
                if(abiturient.id in (select edu_doc.abiturient_id from edu_doc where edu_doc.deleted_at is null and edu_doc.original = 1), 1, 0) as org,
                if(concat(abiturient.id, application.id) in (select concat(consent.abiturient_id, consent.application_id) from consent where consent.deleted_at is null), 1, 0) as agr,
                if(concat(abiturient.id, application.id) in (select concat(abiturient_id, application_id) from contract_info where status_id >= 6), 1, 0) as dog,
                decree.number as decNum, decree.date as decData
          from
            application join abiturient on abiturient.id = application.abiturient_id join competitive_group on competitive_group.id = application.competitive_group_id
                join abiturient_status on abiturient_status.id = abiturient.status_id join side_info on side_info.abiturient_id = abiturient.id
                join specialty on specialty.id = competitive_group.specialty_id left join specialty_profile on specialty_profile.id = competitive_group.profile_id
                join edulevel on edulevel.id = competitive_group.edulevel_id join fintype on fintype.id = competitive_group.fintype_id
                join eduform on eduform.id = competitive_group.eduform_id join post_method on side_info.post_method_id = post_method.id
                left join enrolled on enrolled.abiturient_id = abiturient.id and enrolled.application_id = application.id and enrolled.status_id = 1
                left join decree on decree.id = enrolled.decree_id
                left join consent on application.id = consent.application_id
          where
            application.deleted_at is null  and abiturient.id not in (select abiturient_id from abiturient_lock where user_id = 6)
        ) as base
        limit 0, 100000;
        """

    def get_check_by_query(self, query):
        connection = self._engine.connect()
        df = pd.read_sql(query, connection)
        connection.close()

        return df

    def get_true_spec(self, edu_level, spec_name, profile_name):
        if edu_level != 'Магистратура':
            return spec_name
        return profile_name

    def get_orig_and_agree(self, fintype, post_method, original, agree, dogovor, ss_agr):
        if ss_agr == 1:
            return 1

        if fintype != 'С оплатой обучения':
            if post_method == 'Подано через ЕПГУ':
                return agree
            return original * agree
        return agree * dogovor

    def load_data(self) -> pd.DataFrame:

        # engine = create_engine(
        #     'mysql+pymysql://c3h6o:2m9fpHFVa*Z*UF@172.24.129.190/arm2022'
        # )

        connection = self._engine.connect()
        df = pd.read_sql(self._query, connection, parse_dates={'add_data': '%Y/%m/%d', 'dec_data': '%Y/%m/%d'})
        df['orig_and_agree'] = df.apply(lambda row: self.get_orig_and_agree(row['fintype'], row['post_method'], row['original'], row['agree'], row['dogovor'], row['ss_agr']), axis=1)
        df['spec_name'] = df.apply(
            lambda row: self.get_true_spec(row['edu_level'], row['spec_name'], row['profile_name']), axis=1)

        if 'add_data' in df.columns:
            df['add_data'] = df['add_data'].dt.date

        if 'dec_data' in df.columns:
            df['dec_data'] = df['dec_data'].dt.date

        connection.close()

        self._data = df
        self._load_date = datetime.datetime.now()
        print(df.shape)

        return df

    @property
    def load_date(self):
        return self._load_date

    @property
    def data(self):
        return self._data

class CompareDailyLoader(DailyDataLoader):

    def replace_year(self, date_to_parce):
        today = datetime.date.today()
        parsed = datetime.datetime.strptime(date_to_parce, '%Y-%m-%d').date().replace(year=today.year)
        return parsed

    def __init__(self):
        super(CompareDailyLoader, self).__init__()
        self.last_year_df: pd.DataFrame = pd.read_excel(LAST_YEAR_DATA, parse_dates=True)
        self.last_year_df['add_data'] = pd.to_datetime(self.last_year_df['add_data'])
        self.last_year_df['del_data'] = pd.to_datetime(self.last_year_df['del_data'])
        self.last_year_df['dec_data'] = pd.to_datetime(self.last_year_df['dec_data'])
        self.last_year_df['add_data'] = self.last_year_df['add_data'].dt.date
        self.last_year_df['del_data'] = self.last_year_df['del_data'].dt.date
        self.last_year_df['dec_data'] = self.last_year_df['dec_data'].dt.date
        self.last_year_df['add_data_m_d'] = pd.to_datetime(self.last_year_df['add_data']).dt.strftime('%m-%d')
        self.last_year_df['del_data_m_d'] = pd.to_datetime(self.last_year_df['del_data']).dt.strftime('%m-%d')
        self.last_year_df['dec_data_m_d'] = pd.to_datetime(self.last_year_df['dec_data']).dt.strftime('%m-%d')

    def load_data(self) -> pd.DataFrame:
        super().load_data()

        self._data['add_data_m_d'] = pd.to_datetime(self._data['add_data']).dt.strftime('%m-%d')
        self._data['dec_data_m_d'] = pd.to_datetime(self._data['dec_data']).dt.strftime('%m-%d')
        return self.data


class DataLoader(DailyDataLoader):

    def __init__(self):
        super(DataLoader, self).__init__()
        self._query = '''
select
  base.decree_id, base.ss_agr, base.app_id, base.abId as 'abiturient_id', base.genId as 'gender_id', base.genN as 'gender_name', base.regId as 'region_id', 
  if(base.regId = 0, '-', (select CASE WHEN region.typename = 'г' OR region.typename = 'Респ' THEN CONCAT(region.typename, '. ', region.name) 
  ELSE CONCAT(region.name, ' ', region.typename, '.') END from region where region.id = base.regId)) as 'region_name',
  base.conId as 'country_id', (select country.name from country where country.id = base.conId) as 'country_name', base.specId as 'spec_id', base.specN as 'spec_name', base.specC as 'spec_code', 
  base.specP as 'profile_name', base.eduId as 'edu_level_id', base.eduN as 'edu_level', base.finId as 'fintype_id', base.finN as 'fintype', base.forId as 'edu_from_id', base.forN as 'edu_form', 
  base.posId as 'post_method_id', base.posN as 'post_method', base.org as 'original', base.agr as 'agree', base.dog as 'dogovor', ifnull(base.ex1, 0) as 'disc_point1', 
  ifnull(base.ex2, 0) as 'disc_point2', ifnull(base.ex3, 0) as 'disc_point3', if(base.eduId = 2, if(ifnull(base.ach, 0) > 20, 20, ifnull(base.ach, 0)), if(ifnull(base.ach, 0) > 10, 10, ifnull(base.ach, 0)))  as 'ach'
from 
(select
  consent.sspriem_mark as ss_agr, enrolled.application_id as app_id, enrolled.decree_id as decree_id, ab.id as abId, gender.id as genId, gender.name as genN, ifnull((select region.id from address join region on region.id = address.region_id 
    where ab.id = address.abiturient_id and address.deleted_at is null order by region.id limit 0, 1), 0) as regId,
  ifnull((select country.id from identity_doc join country on country.id = identity_doc.citizenship_id 
    where ab.id = identity_doc.abiturient_id and identity_doc.deleted_at is null order by country.id limit 0, 1), 0) as conId,
    specialty.id as specId, specialty.name as specN, specialty.code as specC, specialty_profile.name as specP, edulevel.id as eduId, edulevel.name as eduN, fintype.id as finId, 
    fintype.name as finN, eduform.id as forId, eduform.name as forN, post_method.id as posId, post_method.name as posN,
    if(ab.id in (select edu_doc.abiturient_id from edu_doc where edu_doc.deleted_at is null and edu_doc.original = 1), 1, 0) as org,
    if(concat(ab.id, application.id) in (select concat(consent.abiturient_id, consent.application_id) from consent where consent.deleted_at is null), 1, 0) as agr,
    if(concat(ab.id, application.id) in (select concat(abiturient_id, application_id) from contract_info where status_id >= 6), 1, 0) as dog,
    (select ifnull(checked_points, points) from abiturient_exam where id = application_exam_cache.exam1_id) as ex1, (select ifnull(checked_points, points) from abiturient_exam where id = application_exam_cache.exam2_id) as ex2,
  (select ifnull(checked_points, points) from abiturient_exam where id = application_exam_cache.exam3_id) as ex3, (select sum(value) from achievement where deleted_at is null and abiturient_id = ab.id) as ach
  from
  application join abiturient as ab on ab.id = application.abiturient_id join competitive_group on competitive_group.id = application.competitive_group_id
    join side_info on side_info.abiturient_id = ab.id join gender on gender.id = side_info.gender_id join specialty on specialty.id = competitive_group.specialty_id 
    left join specialty_profile on specialty_profile.id = competitive_group.profile_id join edulevel on edulevel.id = competitive_group.edulevel_id 
    join fintype on fintype.id = competitive_group.fintype_id join eduform on eduform.id = competitive_group.eduform_id join post_method on side_info.post_method_id = post_method.id
    join application_exam_cache on application_exam_cache.application_id = application.id
    left join enrolled on enrolled.abiturient_id = ab.id and enrolled.application_id = application.id and enrolled.status_id = 1
    left join consent on application.id = consent.application_id and consent.deleted_at is null
  where
  application.deleted_at is null and ab.status_id = 2 and ab.id not in (select abiturient_id from abiturient_lock where user_id = 6) and competitive_group.campaign_id != 3
) as base
limit 0, 100000;
        '''

    def load_kcp(self):
        with open(TOTAL_KCP_FILE, encoding='utf8') as total_kcp_file:
            self.total_kcp_dict: dict = json.load(total_kcp_file)

    def get_mean_point(self, edu_level, disc_point1, disc_point2, disc_point3):
        if edu_level == 'Магистратура':
            return disc_point1
        else:
            return (disc_point1+disc_point2+disc_point3) / 3

    def load_data(self) -> pd.DataFrame:

        df = super().load_data()

        df['point_mean'] = df.apply(lambda row: self.get_mean_point(row['edu_level'], row['disc_point1'], row['disc_point2'], row['disc_point3']), axis=1)

        df['point_sum'] = df['disc_point1'] + df['disc_point2'] + df['disc_point3']
        self._data = df
        self._load_date = datetime.datetime.now()
        self.load_kcp()
        return self.data


if __name__ == '__main__':
    import time

    DAILY_DATA_LOADER = DailyDataLoader()
    DATA_LOADER = DataLoader()
    LAST_DATA_LOADER = CompareDailyLoader()
    df = LAST_DATA_LOADER.load_data()
    df_bal = DATA_LOADER.load_data()
    df_last = LAST_DATA_LOADER.last_year_df

    # for i in range(10):
    #     DATA_LOADER.load_data()
    #     time.sleep(60)
