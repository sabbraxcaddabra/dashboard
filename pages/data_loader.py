import pandas as pd
from sqlalchemy import create_engine
import pymysql
import datetime

class DailyDataLoader:
    _data = None
    _load_date = None
    _engine = create_engine(
            'mysql+pymysql://c3h6o:2m9fpHFVa*Z*UF@172.24.129.190/arm2022'
        )


    _query = """
        select 
          base.abId as 'abiturient_id', base.statId as 'status_id', base.statN as 'status_name', base.genId as 'gender_id', base.genN as 'gender_name', base.hos as 'hostel', base.regId as 'region_id',
            if(base.regId = 0, '-', (select CASE WHEN region.typename = 'г' OR region.typename = 'Респ' THEN CONCAT(region.typename, '. ', region.name) ELSE CONCAT(region.name, ' ', region.typename, '.') END from region where region.id = base.regId))as 'region_name',
            base.conId as 'country_id', (select country.name from country where country.id = base.conId) as 'country_name', base.specId as 'spec_id', base.specN as 'spec_name', base.specC as 'spec_code', base.specP as 'profile_name',
            base.eduId as 'edu_level_id', base.eduN as 'edu_level', base.finId as 'fintype_id', base.finN as 'fintype', base.forId as 'edu_from_id', base.forN as 'edu_form', base.posId as 'post_method_id',
            base.posN as 'post_method', base.tim as 'add_data', base.org as 'original', base.agr as 'agree', base.dog as 'dogovor', 
            ifnull(base.ex1, 0) as 'disc_point1', ifnull(base.ex2, 0) as 'disc_point2', ifnull(base.ex3, 0) as 'disc_point3', ifnull(base.ex1 + base.ex2 + base.ex3, 0) as 'ex_sum'
        from (
        select
          abiturient.id as abId, abiturient_status.id as statId, abiturient_status.name as statN, gender.id as genId, gender.name as genN, side_info.hostel as hos,
            ifnull((select region.id from address join region on region.id = address.region_id where abiturient.id = address.abiturient_id and address.deleted_at is null order by region.id limit 0, 1), 0) as regId,
            ifnull((select country.id from identity_doc join country on country.id = identity_doc.citizenship_id where abiturient.id = identity_doc.abiturient_id and identity_doc.deleted_at is null order by country.id limit 0, 1), 0) as conId,
            specialty.id as specId, specialty.name as specN, specialty.code as specC, specialty_profile.name as specP, edulevel.id as eduId, edulevel.name as eduN, fintype.id as finId, fintype.name as finN,
            eduform.id as forId, eduform.name as forN, post_method.id as posId, post_method.name as posN, application.add_time as tim,
            if(abiturient.id in (select edu_doc.abiturient_id from edu_doc where edu_doc.deleted_at is null and edu_doc.original = 1), 1, 0) as org,
            if(concat(abiturient.id, application.id) in (select concat(consent.abiturient_id, consent.application_id) from consent where consent.deleted_at is null), 1, 0) as agr,
            if(concat(abiturient.id, application.id) in (select concat(abiturient_id, application_id) from contract_info where status_id >= 6), 1, 0) as dog,
          (select points from abiturient_exam where id = application_exam_cache.exam1_id) as ex1,
            (select points from abiturient_exam where id = application_exam_cache.exam2_id) as ex2,
            (select points from abiturient_exam where id = application_exam_cache.exam3_id) as ex3
        from
          application
            join abiturient on abiturient.id = application.abiturient_id
            join specialty on specialty.id = application.specialty_id
            join abiturient_status on abiturient_status.id = abiturient.status_id
            join side_info on side_info.abiturient_id = abiturient.id
            join gender on gender.id = side_info.gender_id
            join edulevel on specialty.level_id = edulevel.id
            join fintype on fintype.id = application.fintype_id
            join eduform on eduform.id = application.eduform_id
            join post_method on post_method.id = side_info.post_method_id
            join application_exam_cache on application_exam_cache.application_id = application.id
      join competitive_group on competitive_group.id = application.competitive_group_id
            left join specialty_profile on specialty_profile.id = competitive_group.profile_id
        where
        application.deleted_at is null and abiturient.id not in (select abiturient_id from abiturient_lock)) as base
        limit 0, 100000;
        """

    def get_true_spec(self, edu_level, spec_name, profile_name):
        if edu_level != 'Магистратура':
            return spec_name
        return profile_name

    def get_orig_and_agree(self, fintype, original, agree, dogovor):
        if fintype != 'С оплатой обучения':
            return original * agree
        else:
            return agree * dogovor

    def load_data(self) -> pd.DataFrame:

        # engine = create_engine(
        #     'mysql+pymysql://c3h6o:2m9fpHFVa*Z*UF@172.24.129.190/arm2022'
        # )

        connection = self._engine.connect()
        df = pd.read_sql(self._query, connection, parse_dates={'add_data': '%Y/%m/%d'})
        df['orig_and_agree'] = df.apply(lambda row: self.get_orig_and_agree(row['fintype'], row['original'], row['agree'], row['dogovor']), axis=1)
        df['spec_name'] = df.apply(
            lambda row: self.get_true_spec(row['edu_level'], row['spec_name'], row['profile_name']), axis=1)
        df['add_data'] = df['add_data'].dt.date
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


class DataLoader(DailyDataLoader):

    def __init__(self):
        super(DataLoader, self).__init__()
        self._query = '''
        select 
          base.abId as 'abiturient_id', base.statId as 'status_id', base.statN as 'status_name', base.genId as 'gender_id', base.genN as 'gender_name', base.hos as 'hostel', base.regId as 'region_id',
            if(base.regId = 0, '-', (select CASE WHEN region.typename = 'г' OR region.typename = 'Респ' THEN CONCAT(region.typename, '. ', region.name) ELSE CONCAT(region.name, ' ', region.typename, '.') END from region where region.id = base.regId))as 'region_name',
            base.conId as 'country_id', (select country.name from country where country.id = base.conId) as 'country_name', base.specId as 'spec_id', base.specN as 'spec_name', base.specC as 'spec_code', base.specP as 'profile_name',
            base.eduId as 'edu_level_id', base.eduN as 'edu_level', base.finId as 'fintype_id', base.finN as 'fintype', base.forId as 'edu_from_id', base.forN as 'edu_form', base.posId as 'post_method_id',
            base.posN as 'post_method', base.tim as 'add_data', base.org as 'original', base.agr as 'agree', base.dog as 'dogovor', 
            ifnull(base.ex1, 0) as 'disc_point1', ifnull(base.ex2, 0) as 'disc_point2', ifnull(base.ex3, 0) as 'disc_point3', ifnull(base.ex1 + base.ex2 + base.ex3, 0) as 'ex_sum'
        from (
        select
          abiturient.id as abId, abiturient_status.id as statId, abiturient_status.name as statN, gender.id as genId, gender.name as genN, side_info.hostel as hos,
            ifnull((select region.id from address join region on region.id = address.region_id where abiturient.id = address.abiturient_id and address.deleted_at is null order by region.id limit 0, 1), 0) as regId,
            ifnull((select country.id from identity_doc join country on country.id = identity_doc.citizenship_id where abiturient.id = identity_doc.abiturient_id and identity_doc.deleted_at is null order by country.id limit 0, 1), 0) as conId,
            specialty.id as specId, specialty.name as specN, specialty.code as specC, specialty_profile.name as specP, edulevel.id as eduId, edulevel.name as eduN, fintype.id as finId, fintype.name as finN,
            eduform.id as forId, eduform.name as forN, post_method.id as posId, post_method.name as posN, application.add_time as tim,
            if(abiturient.id in (select edu_doc.abiturient_id from edu_doc where edu_doc.deleted_at is null and edu_doc.original = 1), 1, 0) as org,
            if(concat(abiturient.id, application.id) in (select concat(consent.abiturient_id, consent.application_id) from consent where consent.deleted_at is null), 1, 0) as agr,
            if(concat(abiturient.id, application.id) in (select concat(abiturient_id, application_id) from contract_info where status_id >= 6), 1, 0) as dog,
          (select points from abiturient_exam where id = application_exam_cache.exam1_id) as ex1,
            (select points from abiturient_exam where id = application_exam_cache.exam2_id) as ex2,
            (select points from abiturient_exam where id = application_exam_cache.exam3_id) as ex3
        from
          application
            join abiturient on abiturient.id = application.abiturient_id
            join specialty on specialty.id = application.specialty_id
            join abiturient_status on abiturient_status.id = abiturient.status_id
            join side_info on side_info.abiturient_id = abiturient.id
            join gender on gender.id = side_info.gender_id
            join edulevel on specialty.level_id = edulevel.id
            join fintype on fintype.id = application.fintype_id
            join eduform on eduform.id = application.eduform_id
            join post_method on post_method.id = side_info.post_method_id
            join application_exam_cache on application_exam_cache.application_id = application.id
      join competitive_group on competitive_group.id = application.competitive_group_id
            left join specialty_profile on specialty_profile.id = competitive_group.profile_id
        where
        application.deleted_at is null and abiturient.status_id = 2 and abiturient.id not in (select abiturient_id from abiturient_lock)) as base
        limit 0, 100000;
        '''
    def get_mean_point(self, edu_level, disc_point1, disc_point2, disc_point3):
        if edu_level == 'Магистратура':
            return disc_point1
        else:
            return (disc_point1+disc_point2+disc_point3) / 3

    def load_data(self) -> pd.DataFrame:
        # connection = self._engine.connect()
        # df = pd.read_sql(self._query, connection, parse_dates={'add_data': '%Y/%m/%d'})
        # # df['orig_and_agree'] = df.apply(
        # #     lambda row: self.get_orig_and_agree(row['fintype'], row['original'], row['agree'], row['dogovor']), axis=1)
        # df['add_data'] = df['add_data'].dt.date
        # connection.close()

        df = super().load_data()

        df['point_mean'] = df.apply(lambda row: self.get_mean_point(row['edu_level'], row['disc_point1'], row['disc_point2'], row['disc_point3']), axis=1)
        # df = df[df['point_mean'] > 0]
        self._data = df
        self._load_date = datetime.datetime.now()
        return self.data


if __name__ == '__main__':
    import time

    DAILY_DATA_LOADER = DailyDataLoader()
    DATA_LOADER = DataLoader()
    df = DAILY_DATA_LOADER.load_data()
    df_bal = DATA_LOADER.load_data()

    # for i in range(10):
    #     DATA_LOADER.load_data()
    #     time.sleep(60)
