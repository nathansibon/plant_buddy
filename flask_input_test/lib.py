import sqlite3 as sql
import pandas as pd
from datetime import date

# read requirements database to feed into functions below
def read_req_db():

    con = sql.connect('plant_requirements.db')
    cur = con.cursor()

    req = pd.read_sql_query('SELECT * FROM requirements', con)
    key = pd.read_sql_query('SELECT * FROM key', con)
    combined_name = (req['common_name'] + ' (' + req['botanical_name'] + ')').tolist()

    return (req, key, combined_name)


(req, key, combined_name) = read_req_db()

#for index, row in req.iterrows():
#    print(row['common_name'])


# specific functions for webpages
def get_form_data(in_list):

    output = []

    for i in range(len(in_list) - 1):  # must be len()-1 to remove submit
        try:
            output.append(int(in_list[i]))
        except Exception as e:
            try:
                output.append(float(in_list[i]))
            except:
                output.append(in_list[i])
                continue

    return output


def add_last_plant_vars():
    #fields are: last watered, need water, has pic, ignore, death (all are bool), last re-pot date
    output = [0, 0, 0, 0, 0, date.today().strftime('%Y/%m/%d')]
    return output


def init_database(database):

    con = sql.connect(str(database)+'.db')
    con.execute('CREATE TABLE IF NOT EXISTS houseplants ('
                'ID INTEGER PRIMARY KEY AUTOINCREMENT,'
                'name varchar(765),'
                'species varchar(765),'
                'location varchar(765),'
                'purchase_date timestamp,'
                'pot_size real,'
                'leaf_temp_offset real,'
                'last_watered smallint,'
                'need_water smallint,'
                'has_pic smallint,'
                'ignore smallint,'
                'death smallint,'
                'last_repot_date timestamp)')
    con.close()


def read_row(database, table, id_column, id):

    # Returns the column names and values for a single entry via the row id

    try:
        database = str(database)
        table = str(table)
        id_column = str(id_column)
        id = str(id)
    except Exception as e:
        print(e)

    con = sql.connect(database + '.db')
    cur = con.cursor()

    cur.execute('PRAGMA table_info(' + table +')')
    temp_columns = cur.fetchall()
    columns = []
    for tuple in temp_columns:
        columns.append(tuple[1])
    print(columns)

    # returns a tuple of table names in this database
    cur.execute('SELECT * FROM ' + table + ' WHERE ' + id_column + ' = ' + id)

    # returns list of rows
    row = cur.fetchall()

    if row == []:
        print('Error: No plant with ID ' + id)
    else:
        print(row)

    con.close()

    return (columns, row[0]) # need to do row[0] instead of just row since the cursor returns a tuple of lists (we just need the list)


def read_plant():
    con = sql.connect('my_plants.db')
    cur = con.cursor()

    cur.execute('PRAGMA table_info(houseplants)')
    columns = cur.fetchall()

    # returns a tuple of table names in this database
    cur.execute('SELECT * FROM houseplants')

    # returns list of rows
    rows = cur.fetchall()

    if rows == []:
        print('you have no plants, how sad! :(')

    con.close()

    return (columns, rows)

def add_plant_to_database(database, result):

    print(type(result))
    print(result)
    try:
        con = sql.connect(str(database)+'.db')
        cur = con.cursor()
        cur.execute('INSERT INTO houseplants('
                  'name, '
                  'species,'
                  'location, '
                  'purchase_date, '
                  'pot_size, '
                  'leaf_temp_offset,'
                  'last_watered,'
                  'need_water,'
                  'has_pic,'
                  'ignore,'
                  'death,'
                  'last_repot_date)'
                  'VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                  result)
        con.commit()

    except con.Error as err:
        print(err)

    finally:
        con.close()


def update_plant(id, new_values):

    # cur.execute can only take 2 arguments so we need to add the ID to the list
    new_values.append(id)

    con = sql.connect('my_plants.db')
    cur = con.cursor()

    cur.execute('UPDATE houseplants '
                'SET '
                'name = ?, '
                'species = ?,'
                'location = ?, '
                'purchase_date = ?, '
                'pot_size = ?, '
                'leaf_temp_offset = ?,'
                'last_repot_date = ?'
                'WHERE ID = ?', new_values)

    con.commit()
    con.close()

def read_req():

    con = sql.connect('plant_requirements.db')
    cur = con.cursor()

    cur.execute('PRAGMA table_info(requirements)')
    columns = cur.fetchall()
    print(columns)

    # returns a tuple of table names in this database
    cur.execute('SELECT * FROM requirements')

    # returns list of rows
    rows = cur.fetchall()

    if rows == []:
        print('Requirements database is empty!')
    else:
        for row in rows:
            print(row)

    con.close()

    return (columns, rows)


def add_req(result):

    print('start conversion')
    print(result)
    # process input from webpage - convert text descriptions to numeric keys and calculate tolerances
    t = [result.get('species'), result.get('common_name')]

    t.append(float(key[(key['light'] == result.get('light_low')) | (key['light'] == result.get('light_high'))].category.mean()))
    t.append(float(abs(key[key['light'] == result.get('light_high')].category.values[0] - key[key['light'] == result.get('light_low')].category.values[0])))

    t.append(float(key[(key['temp'] == result.get('temp_low')) | (key['temp'] == result.get('temp_high'))].category.mean()))
    t.append(float(abs(key[key['temp'] == result.get('temp_high')].category.values[0] - key[key['temp'] == result.get('temp_low')].category.values[0])))

    t.append(float(key[(key['rh'] == result.get('rh_low')) | (key['rh'] == result.get('rh_high'))].category.mean()))
    t.append(float(abs(key[key['rh'] == result.get('rh_high')].category.values[0] - key[key['rh'] == result.get('rh_low')].category.values[0])))

    t.append(float(key[(key['water'] == result.get('water_low')) | (key['water'] == result.get('water_high'))].category.mean()))
    t.append(float(abs(key[key['water'] == result.get('water_high')].category.values[0] - key[key['water'] == result.get('water_low')].category.values[0])))

    t.append(float(key[key['soil'] == 'Foliage plants'].category.values[0]))

    try:
        con = sql.connect('plant_requirements.db')
        c = con.cursor()
        c.execute('INSERT INTO requirements('
                  'botanical_name, '
                  'common_name,'
                  'light_category,'
                  'light_tolerance,'
                  'temp_category,'
                  'temp_tolerance,'
                  'rh_category,'
                  'rh_tolerance,'
                  'water_category,'
                  'water_tolerance,'
                  'soil_category)'
                  'VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                  t)
        con.commit()

    except con.Error as err:
        print(err)

    finally:
        con.close()