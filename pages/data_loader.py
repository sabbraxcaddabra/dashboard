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
    base.conId as 'country_id', (select country.name from country where country.id = base.conId) as 'country_name', base.specId as 'spec_id', base.specN as 'spec_name', base.specC as 'spec_code',
    base.eduId as 'edu_level_id', base.eduN as 'edu_level', base.finId as 'fintype_id', base.finN as 'fintype', base.forId as 'edu_from_id', base.forN as 'edu_form', base.posId as 'post_method_id',
    base.posN as 'post_method', base.tim as 'add_data', base.org as 'original', base.agr as 'agree', base.dog as 'dogovor'
from (
select
  abiturient.id as abId, abiturient_status.id as statId, abiturient_status.name as statN, gender.id as genId, gender.name as genN, side_info.hostel as hos,
    ifnull((select region.id from address join region on region.id = address.region_id where abiturient.id = address.abiturient_id and address.deleted_at is null order by region.id limit 0, 1), 0) as regId,
    ifnull((select country.id from identity_doc join country on country.id = identity_doc.citizenship_id where abiturient.id = identity_doc.abiturient_id and identity_doc.deleted_at is null order by country.id limit 0, 1), 0) as conId,
    specialty.id as specId, specialty.name as specN, specialty.code as specC, edulevel.id as eduId, edulevel.name as eduN, fintype.id as finId, fintype.name as finN,
    eduform.id as forId, eduform.name as forN, post_method.id as posId, post_method.name as posN, application.add_time as tim,
    if(abiturient.id in (select edu_doc.abiturient_id from edu_doc where edu_doc.deleted_at is null and edu_doc.original = 1), 1, 0) as org,
    if(concat(abiturient.id, application.id) in (select concat(consent.abiturient_id, consent.application_id) from consent where consent.deleted_at is null), 1, 0) as agr,
    if(concat(abiturient.id, application.id) in (select concat(abiturient_id, application_id) from contract_info), 1, 0) as dog
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
where 
  application.deleted_at is null) as base
limit 0, 100000;
        """

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
        SELECT * FROM 
        (SELECT
            ab.id as abiturient_id,
            ab.status_id as status_id,
            ab_s.name as status_name,
            side.gender_id as gender_id,
            gender.name as gender_name,
            side.hostel as hostel,
            app.specialty_id,
        region.id as region_id,
        CASE
            WHEN region.typename = 'г' OR region.typename = 'Респ' THEN CONCAT(region.typename, '. ', region.name)
            ELSE CONCAT(region.name, ' ', region.typename, '.')
        END as region_name,
            country.id as country_id, 
            country.name as country_name,
            spec.id as spec_id, 
            spec.name as spec_name, 
            spec.code as spec_code, 
            spec.level_id as edu_level_id,
            el.name as edu_level, 
        app.fintype_id as fintype_id, 
            fin.name as fintype, 
            app.eduform_id as edu_form_id, 
            edu.name as edu_form,
            side.post_method_id as post_method_id, 
            pm.name as post_method, 
            app.add_time as add_data, 
            IF((SELECT COUNT(ed.id) FROM edu_doc as ed WHERE ed.abiturient_id = app.abiturient_id AND ed.deleted_at IS NOT NULL) = 0, 0, 1) as original,
            (SELECT MAX(ab_e.points) FROM abiturient_exam as ab_e JOIN discipline as dis ON ab_e.discipline_id = dis.id
            JOIN admission_direction_exam as ad_e ON ad_e.discipline_id = dis.id WHERE ab_e.abiturient_id = ab.id AND 
                (SELECT ad_es.id FROM admission_direction_exam_slot as ad_es WHERE ad_es.admission_direction_id = ad_d.id AND ad_es.id = ad_e.slot_id AND ad_es.priority = 1) IS NOT NULL) as disc_point1,    
            (SELECT MAX(ab_e.points) FROM abiturient_exam as ab_e JOIN discipline as dis ON ab_e.discipline_id = dis.id
            JOIN admission_direction_exam as ad_e ON ad_e.discipline_id = dis.id WHERE ab_e.abiturient_id = ab.id AND 
                (SELECT ad_es.id FROM admission_direction_exam_slot as ad_es WHERE ad_es.admission_direction_id = ad_d.id AND ad_es.id = ad_e.slot_id AND ad_es.priority = 2) IS NOT NULL) as disc_point2,
        (SELECT MAX(ab_e.points) FROM abiturient_exam as ab_e JOIN discipline as dis ON ab_e.discipline_id = dis.id
            JOIN admission_direction_exam as ad_e ON ad_e.discipline_id = dis.id WHERE ab_e.abiturient_id = ab.id AND 
                (SELECT ad_es.id FROM admission_direction_exam_slot as ad_es WHERE ad_es.admission_direction_id = ad_d.id AND ad_es.id = ad_e.slot_id AND ad_es.priority = 3) IS NOT NULL) as disc_point3
                
        FROM application as app 
        JOIN abiturient as ab ON ab.id = app.abiturient_id
            JOIN admission_direction as ad_d ON 
            IF(app.profile_id IS NULL, app.specialty_id = ad_d.specialty_id, app.specialty_id = ad_d.specialty_id AND app.profile_id = ad_d.profile_id)
        JOIN abiturient_status as ab_s ON ab_s.id = ab.status_id
            JOIN side_info as side ON side.abiturient_id = ab.id
            JOIN gender ON gender.id = side.gender_id
        JOIN address as ad ON ad.abiturient_id = ab.id LEFT JOIN region ON region.id = ad.region_id
        JOIN identity_doc as iden ON iden.abiturient_id = ab.id
        JOIN country ON country.id = iden.citizenship_id
            JOIN specialty as spec ON spec.id = app.specialty_id
        JOIN edulevel as el ON el.id = spec.level_id 
        JOIN fintype as fin ON fin.id = app.fintype_id
            JOIN eduform as edu ON edu.id = app.eduform_id
            JOIN post_method as pm ON pm.id = side.post_method_id

        WHERE ad_d.campaign_id !=3 AND side.campaign_id != 3 AND ad.type_id = 1 AND ad.deleted_at IS NULL AND iden.status = 1
        ) as allO
        WHERE IF(edu_level_id != 2, IF(disc_point1 = 0 OR disc_point1 IS NULL OR disc_point2 = 0 OR disc_point2 IS NULL OR disc_point3 = 0 OR disc_point3 IS NULL, false, true), IF(disc_point1 = 0 OR disc_point1 IS NULL, false, true))
        LIMIT 0, 100000;
        '''
    def get_mean_point(self, edu_level, disc_point1, disc_point2, disc_point3):
        if edu_level == 'Магистратура':
            return disc_point1
        else:
            return (disc_point1+disc_point2+disc_point3) / 3

    def load_data(self) -> pd.DataFrame:
        connection = self._engine.connect()
        df = pd.read_sql(self._query, connection, parse_dates={'add_data': '%Y/%m/%d'})
        # df['orig_and_agree'] = df.apply(
        #     lambda row: self.get_orig_and_agree(row['fintype'], row['original'], row['agree'], row['dogovor']), axis=1)
        df['add_data'] = df['add_data'].dt.date
        connection.close()
        print(df.shape)
        df['point_mean'] = df.apply(lambda row: self.get_mean_point(row['edu_level'], row['disc_point1'], row['disc_point2'], row['disc_point3']), axis=1)
        self._data = df
        self._load_date = datetime.datetime.now()
        return self.data


if __name__ == '__main__':
    import time

    DAILY_DATA_LOADER = DailyDataLoader()
    DATA_LOADER = DataLoader()
    df = DAILY_DATA_LOADER.load_data()

    # for i in range(10):
    #     DATA_LOADER.load_data()
    #     time.sleep(60)
