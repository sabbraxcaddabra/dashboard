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
        SELECT app.abiturient_id as abiturient_id, ab.status_id as status_id, ab_s.name as status_name, side.gender_id as gender_id, gender.name as gender_name, side.hostel as hostel, region.id as region_id,
        CASE
            WHEN region.typename = 'г' OR region.typename = 'Респ' THEN CONCAT(region.typename, '. ', region.name)
            ELSE CONCAT(region.name, ' ', region.typename, '.')
        END as region_name
        , country.id as country_id, country.name as country_name, spec.id as spec_id, spec.name as spec_name, spec.code as spec_code, spec.level_id as edu_level_id, el.name as edu_level, 
        app.fintype_id as fintype_id, fin.name as fintype, app.eduform_id as edu_form_id, edu.name as edu_form, side.post_method_id as post_method_id, pm.name as post_method, app.add_time as add_data, ed.original as original
        FROM application as app JOIN specialty as spec ON spec.id = app.specialty_id
            JOIN edulevel as el ON el.id = spec.level_id JOIN fintype as fin ON fin.id = app.fintype_id
            JOIN eduform as edu ON edu.id = app.eduform_id JOIN side_info as side ON side.abiturient_id = app.abiturient_id
            JOIN post_method as pm ON pm.id = side.post_method_id JOIN edu_doc as ed ON ed.abiturient_id = app.abiturient_id
            JOIN abiturient as ab ON ab.id = app.abiturient_id JOIN abiturient_status as ab_s ON ab_s.id = ab.status_id
        JOIN address as ad ON ad.abiturient_id = ab.id LEFT JOIN region ON region.id = ad.region_id JOIN identity_doc as iden ON iden.abiturient_id = ab.id
            JOIN country ON country.id = iden.citizenship_id JOIN gender ON gender.id = side.gender_id
        WHERE side.campaign_id != 3 AND ad.type_id = 1 AND ad.deleted_at IS NULL AND iden.status != 0
        ORDER BY add_data DESC, spec_id
        LIMIT 0, 100000;
        """

    def load_data(self) -> pd.DataFrame:

        # engine = create_engine(
        #     'mysql+pymysql://c3h6o:2m9fpHFVa*Z*UF@172.24.129.190/arm2022'
        # )

        connection = self._engine.connect()
        df = pd.read_sql(self._query, connection, parse_dates={'add_data': '%Y/%m/%d'})
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

        WHERE ad_d.campaign_id !=3 AND ad.type_id = 1 AND ad.deleted_at IS NULL AND iden.status = 1
        ) as allO
        WHERE IF(edu_level_id != 2, IF(disc_point1 = 0 OR disc_point1 IS NULL OR disc_point2 = 0 OR disc_point2 IS NULL OR disc_point3 = 0 OR disc_point3 IS NULL, false, true), IF(disc_point1 = 0 OR disc_point1 IS NULL, false, true))
        LIMIT 0, 100000;
        '''

    def load_data(self) -> pd.DataFrame:
        super(DataLoader, self).load_data()
        self._data['point_mean'] = (self._data['disc_point1'] + self._data['disc_point2'] + self._data['disc_point3']) / 3
        return self.data


if __name__ == '__main__':
    import time

    DATA_LOADER = DataLoader()
    # for i in range(10):
    #     DATA_LOADER.load_data()
    #     time.sleep(60)
