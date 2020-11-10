import json
import re
import sqlite3

import pandas as pd

import database_validation

db_url = "cemetery.db"


def validate_cemetery_name(cemetery_name: str) -> bool:
    pattern = re.compile('^[a-zA-Z ]+$')
    if cemetery_name and re.match(pattern, cemetery_name):
        return True
    print("Cemetery name may only contain alphabetical characters or spaces.")
    return False


def create_table(tablename: str) -> None:
    conn = sqlite3.connect(db_url)
    c = conn.cursor()
    try:
        create = f'''CREATE TABLE IF NOT EXISTS {tablename} 
            (id INTEGER UNIQUE, row INTEGER, col INTEGER, 
            toplx FLOAT, toply FLOAT, toprx FLOAT, topry FLOAT, 
            botlx FLOAT, botly FLOAT, botrx FLOAT, botry FLOAT,
            centroidx FLOAT, centroidy FLOAT);'''
        c.execute(create)
    except conn.Error as e:
        conn.commit()
        conn.close()
        print(e)
        return
    except:
        conn.commit()
        conn.close()
        print("Unknown Error Occured")
        return
    conn.commit()
    conn.close()


def get_gravestones(tablename: str):
    conn = sqlite3.connect(db_url)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {tablename}", conn)
    except conn.Error as e:
        conn.commit()
        conn.close()
        print(e)
        return
    except:
        conn.commit()
        conn.close()
        print("Unknown Error Occured")
        return
    conn.commit()
    conn.close()

    return df


def export_table(tablename: str, output_filename: str) -> None:
    df = get_gravestones(tablename)
    properties = ['id', 'row', 'col', 'centroid']
    geojson = df_to_geojson(df, properties)
    with open(output_filename, 'w') as output_file:
        json.dump(geojson, output_file, indent=2)


def df_to_geojson(df, properties, toplx='toplx', toply='toply', toprx='toprx', topry='topry', botlx='botlx',
                  botly='botly', botrx='botrx', botry='botry', centroidx='centroidx', centroidy='centroidy') -> dict:
    geojson = {'type': 'FeatureCollection', 'name': "Arlington", 'features': []}
    for _, row in df.iterrows():
        feature = {'type': 'Feature', 'properties': {}, 'geometry': {'type': 'MultiPolygon', 'coordinates': []}}
        feature['geometry']['coordinates'] = [
            [[row[toplx], row[toply]], [row[toprx], row[topry]], [row[botlx], row[botly]], [row[botrx], row[botry]],
             [row[toplx], row[toply]]]]
        for prop in properties:
            if prop == 'id' or prop == 'row' or prop == 'col':
                feature['properties'][prop] = int(row[prop]) if row[prop] is not None else None
            elif prop == 'centroid':
                feature['properties'][prop] = [row[centroidx], row[centroidy]]
            else:
                feature['properties'][prop] = row[prop]
        geojson['features'].append(feature)
    return geojson


def add_entry(tablename: str, id: int, row: int, col: int, toplx: float, toply: float, toprx: float, topry: float,
              botlx: float, botly: float, botrx: float, botry: float, centroidx: float, centroidy: float) -> None:
    # id, row, col, toplx, toply, toprx, topry, botlx, botly, botrx, botry, centroidx, centroidy = values.split(',')
    if not database_validation.isValidID(id):
        return
    if not database_validation.isValidOrder(row) or not database_validation.isValidOrder(col):
        return
    if not database_validation.isValidCoord(toplx) or not database_validation.isValidCoord(
            toply) or not database_validation.isValidCoord(toprx) or not database_validation.isValidCoord(
        topry) or not database_validation.isValidCoord(
        botlx) or not database_validation.isValidCoord(botly) or not database_validation.isValidCoord(
        botrx) or not database_validation.isValidCoord(botry) or not database_validation.isValidCoord(
        centroidx) or not database_validation.isValidCoord(centroidy):
        return
    conn = sqlite3.connect(db_url)
    c = conn.cursor()
    try:
        add = f"INSERT OR REPLACE INTO {tablename} VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);"
        c.execute(add, (id, row, col, toplx, toply, toprx, topry, botlx, botly, botrx, botry, centroidx, centroidy))
    except conn.Error as e:
        conn.commit()
        conn.close()
        print(e)
        return
    except:
        conn.commit()
        conn.close()
        print("Unknown Error Occured")
        return
    conn.commit()
    conn.close()
