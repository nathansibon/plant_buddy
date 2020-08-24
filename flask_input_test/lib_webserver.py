import sqlite3 as sql
import pandas as pd
import numpy as np
from datetime import date, datetime
import os
from pathlib import Path


# read requirements database to feed into functions below
def read_req_db():

    con = sql.connect('plant_requirements.db')
    cur = con.cursor()

    req = pd.read_sql_query('SELECT * FROM requirements', con)
    key = pd.read_sql_query('SELECT * FROM key', con)
    combined_name = (req['common_name'] + ' (' + req['botanical_name'] + ')').tolist()
    soil_choice = (key['soil']).tolist()

    return (req, key, combined_name, soil_choice)


(req, key, combined_name, soil_choice) = read_req_db()


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


def init_database(database):

    con = sql.connect(str(database)+'.db')

    # create table houseplants
    con.execute('CREATE TABLE IF NOT EXISTS houseplants ('
                'ID INTEGER PRIMARY KEY AUTOINCREMENT,' # 0
                'name varchar(765),'                    # 1
                'species varchar(765),'                 # 2
                'location varchar(765),'                # 3
                'purchased_from varchar(765),'          # 4
                'purchase_date timestamp,'              # 5
                'water_schedule_in_days integer,'       # 6
                'last_watered timestamp,'               # 7
                'substrate varchar(765),'               # 8
                'pot_size real,'                        # 9
                'leaf_temp_offset integer,'             # 10
                'pic_path varchar(765),'                # 11
                'has_pic smallint,'                     # 12
                'days_since_last_water integer,'        # 13
                'need_water smallint,'                  # 14
                'water_warning smallint,'               # 15
                'ignore smallint,'                      # 16
                'death smallint,'                       # 17
                'last_repot_date timestamp)')           # 18

    # create table my_journal
    con.execute('CREATE TABLE IF NOT EXISTS journal ('
                'ID INTEGER PRIMARY KEY AUTOINCREMENT,' # 0
                'date timestamp, '                      # 1
                'title varchar(765),'                   # 2
                'plant varchar(765),'                   # 3
                'body text,'                            # 4
                'has_pic smallint,'                     # 5
                'pic_path varchar(765))')               # 6

    con.close()

def get_db_tables(database):

    database = str(database)
    print(database)

    con = sql.connect(database)
    cur = con.cursor()

    cur.execute('SELECT name FROM sqlite_master WHERE type="table";')
    temp_tbl = cur.fetchall()
    tables = []
    for tuple in temp_tbl:
        if tuple[0] == 'sqlite_sequence':
            pass
        else:
            tables.append(tuple[0])
    print(tables)

    return tables

def read_row(database, table, id_column, id):

    # Returns the column names and values for a single entry via the row id

    try:
        database = str(database)
        table = str(table)
        id_column = str(id_column)
        id = str(id)
        print(database, table, id_column, id)
    except Exception as e:
        print(e)

    con = sql.connect(database)
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

def read_sql(database, query):

    print('--------Start Database Query--------')
    print('Query:' + query)
    database = str(database)
    print(database)

    con = sql.connect(database)
    cur = con.cursor()

    # change query into a list of strings to extract which columns are returned (otherwise display table won't have headers)
    temp_list = query.split()
    print('requested columns:')
    query_list = []
    for item in temp_list:
        query_list.append(item.strip(','))
    print(query_list)

    # find the table being queried
    for i in range(len(query_list)):
        if query_list[i] == 'from':
            table = query_list[i + 1]

    # get a list of all columns in the table
    cur.execute('PRAGMA table_info(' + table + ')')
    temp_columns = cur.fetchall()
    all_columns = []
    for tuple in temp_columns:
        all_columns.append(tuple[1])
    print('all columns:')
    print(all_columns)

    if '*' in query_list:
        columns = all_columns
    else:
        columns = []
        # gather list of columns being queried using the query-list and the list of all columns
        for item in all_columns:
            if item in query_list:
                print(item)
                columns.append(item)

    # finally, get the query result
    cur.execute(query)
    rows = cur.fetchall()

    return (columns, rows)


def read_all(table):
    print('----Starting read all----')
    con = sql.connect('my_plants.db')
    cur = con.cursor()

    cur.execute('PRAGMA table_info(' + str(table) + ')')
    columns = cur.fetchall()

    # returns a tuple of table names in this database
    cur.execute('SELECT * FROM ' + str(table))

    # returns list of rows
    rows = list(cur.fetchall())

    if rows == []:
        print('table is empty :(')
    else:
        for row in rows:
            row = list(row)

    con.close()

    return (columns, rows)

def add_plant_to_database(result):

    print('----Starting add plant to db----')
    print(result)

    # add last plant vars
    last = [
        pd.Timestamp.now() - pd.Timestamp(result[6]), # days_since_last_water
        0, # need water
        0, # water_warning
        0, # ignore
        0, # death
        date.today().strftime('%Y/%m/%d') # last re-pot date
        ]

    if last[0] >= pd.Timedelta(str(result[5]) + ' days'): # days_since_last_water > watering_schedule_in_days
        last[1] = 1 # need water = true
    elif pd.Timedelta(str(result[5]) + ' days') - last[0] < pd.Timedelta('3 days'): # watering_schedule_in_days - days_since_last_water
        last[2] = 1 # if less than 3 days until needs water, set warning to True
    last[0] = last[0].days # set days_since_last_water back to integer from Pandas Timedelta

    for i in last:
        result.append(i)

    print(result)

    try:
        con = sql.connect('my_plants.db')
        cur = con.cursor()
        cur.execute('INSERT INTO houseplants('
                  'name, '
                  'species,'
                  'location, '
                  'purchased_from,'
                  'purchase_date, '
                  'water_schedule_in_days,'
                  'last_watered,'
                  'substrate,'
                  'pot_size,'
                  'leaf_temp_offset,'
                  'pic_path,'
                  'has_pic,'
                  'days_since_last_water,'
                  'need_water,'
                  'water_warning,'
                  'ignore,'
                  'death,'
                  'last_repot_date)'
                  'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  result)
        con.commit()

    except con.Error as err:
        print(err)

    finally:
        con.close()

def update_plant(id, new_values):

    print('----Starting update plant----')
    # cur.execute can only take 2 arguments so we need to add the ID to the list
    print(new_values)

    last = [
        pd.Timestamp.now() - pd.Timestamp(new_values[2]),  # days_since_last_water
        0,  # need water
        0,  # water_warning
    ]

    if last[0] >= pd.Timedelta(str(new_values[1]) + ' days'): # days_since_last_water > watering_schedule_in_days
        last[1] = 1 # need water = true
    elif pd.Timedelta(str(new_values[1]) + ' days') - last[0] < pd.Timedelta('3 days'): # watering_schedule_in_days - days_since_last_water
        last[2] = 1 # if less than 3 days until needs water, set warning to True
    last[0] = last[0].days # set days_since_last_water back to integer from Pandas Timestamp

    for i in last:
        new_values.append(i)

    new_values.append(id)
    print(new_values)

    con = sql.connect('my_plants.db')
    cur = con.cursor()

    cur.execute('UPDATE houseplants '
                'SET '
                'location = ?, '
                'water_schedule_in_days = ?,'
                'last_watered = ?,'
                'substrate = ?,'
                'pot_size = ?,'
                'leaf_temp_offset = ?,'
                'last_repot_date = ?,'
                'pic_path = ?,'
                'has_pic = ?,'
                'days_since_last_water = ?,'
                'need_water = ?,'
                'water_warning = ?'
                'WHERE ID = ?', new_values)

    con.commit()
    con.close()



def del_plant(id):

    print('----Deleting plant----')
    print('id = ' + str(id))

    con = sql.connect('my_plants.db')
    cur = con.cursor()

    cur.execute('DELETE FROM houseplants WHERE ID = ' + str(id))

    con.commit()
    con.close()


def plant_image_exists(plant_name):
    # checks if an image file exists for plant, if so returns the filename
    # plant_name is the result[0] from the html form

    img_filename = 'plant_img_' + plant_name

    all_files = []
    for (dirpath, dirnames, filenames) in os.walk(Path.cwd() / 'static'):
        all_files.extend(filenames)
        break

    for file in all_files:
        if file.startswith(img_filename):
            return file

    return False


def del_plant_image(plant_name):
    #  plant_name is the result[0] from the html form

    img_filename = 'plant_img_' + plant_name

    all_files = []
    for (dirpath, dirnames, filenames) in os.walk(Path.cwd() / 'static'):
        all_files.extend(filenames)
        break

    for file in all_files:
        if file.startswith(img_filename):
            os.remove(Path(Path.cwd() / 'static' / file))
            return True

    return False


def get_all_plant_data(database, plant):

    import sqlite3 as sql # i have no idea why this is needed given global import above, but python gave a 'referenced before assignment' error without it...
    cols = ['drybulb', 'rh', 'vpd', 'lux']

    con = sql.connect(database + '_data.db')
    cur = con.cursor()

    sql = 'SELECT * FROM indoor_raw WHERE location="' + str(plant) + '"'
    print(sql)
    raw_data = pd.read_sql_query(sql, con)
    print(raw_data)
    result = {}

    for i in cols:
        result[str(i + '_mean')] = np.round(raw_data[i].mean(), 1)
        result[str(i + '_max')] = np.round(raw_data[i].max(), 1)
        result[str(i + '_min')] = np.round(raw_data[i].min(), 1)
        result[str(i + '_q_10')] = np.round(raw_data[i].quantile(0.1), 1)
        result[str(i + '_q_90')] = np.round(raw_data[i].quantile(0.9), 1)

    return result


def water_plant(id):

    print('----Starting water plant----')

    con = sql.connect('my_plants.db')
    cur = con.cursor()

    if id == 'all':
        print('water all')
        cur.execute('SELECT ID FROM houseplants')
        ids = cur.fetchall() # recall fetch annoyingly returns a list of tuples, so we need to access the tuple item to get the raw value...

        for item in ids:
            print(item[0])
            cur.execute('UPDATE houseplants SET last_watered = ?, need_water = ?, water_warning = ? WHERE ID = ?',
                        [datetime.today().strftime('%Y-%m-%d'), 0, 0, item[0]])
    else:
        print('water one, id= ' + str(id))
        cur.execute('UPDATE houseplants SET last_watered = ?, need_water = ?, water_warning = ? WHERE ID = ?',
                    [datetime.today().strftime('%Y-%m-%d'), 0, 0, id])

    con.commit()
    con.close()


def del_entry(id):

    print('----Deleting Journal Entry----')
    print('id = ' + str(id))

    con = sql.connect('my_plants.db')
    cur = con.cursor()

    cur.execute('DELETE FROM journal WHERE ID = ' + str(id))

    con.commit()
    con.close()


def journal_image_exists(name):
    # checks if an image file exists for plant, if so returns the filename
    # plant_name is the result[0] from the html form

    print('-----Deleting Journal Picture-----')
    img_filename = 'journal_img_' + name
    print(img_filename)
    all_files = []
    for (dirpath, dirnames, filenames) in os.walk(Path.cwd() / 'static'):
        all_files.extend(filenames)
        break

    for file in all_files:
        if file.startswith(img_filename):
            return True

    return False


def del_journal_image(name):
    #  plant_name is the result[0] from the html form

    img_filename = 'journal_img_' + name

    all_files = []
    for (dirpath, dirnames, filenames) in os.walk(Path.cwd() / 'static'):
        all_files.extend(filenames)
        break

    for file in all_files:
        if file.startswith(img_filename):
            os.remove(Path(Path.cwd() / 'static' / file))
            return True

    return False


def read_req():

    print('----Starting read requirements----')

    con = sql.connect('plant_requirements.db')
    cur = con.cursor()

    cur.execute('PRAGMA table_info(requirements)')
    columns = cur.fetchall()
    print(columns[1])

    # returns a tuple of table names in this database
    cur.execute('SELECT * FROM requirements')

    # returns list of rows
    rows = cur.fetchall()

    if rows == []:
        print('Requirements database is empty!')
    else:
        print(rows[0])

    con.close()

    return (columns, rows)


def add_journal_db(result):

    print('----Starting add journal to db----')
    print(result)

    try:
        con = sql.connect('my_plants.db')
        cur = con.cursor()
        cur.execute('INSERT INTO journal('
                  'date,'
                  'title,'
                  'plant,'
                  'body,'
                  'has_pic,'
                  'pic_path)'
                  'VALUES (?,?,?,?,?,?)',
                  result)
        con.commit()

    except con.Error as err:
        print(err)

    finally:
        con.close()


def add_req(result):

    print('----Starting add requirement----')

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

def update_req(id, new_values):

    print('----Starting read requirement----')

    print('start conversion')
    print(new_values)
    # process input from webpage - convert text descriptions to numeric keys and calculate tolerances
    t = [new_values.get('species'), new_values.get('common_name')]

    t.append(float(
        key[(key['light'] == new_values.get('light_low')) | (key['light'] == new_values.get('light_high'))].category.mean()))
    t.append(float(abs(key[key['light'] == new_values.get('light_high')].category.values[0] -
                       key[key['light'] == new_values.get('light_low')].category.values[0])))

    t.append(
        float(key[(key['temp'] == new_values.get('temp_low')) | (key['temp'] == new_values.get('temp_high'))].category.mean()))
    t.append(float(abs(key[key['temp'] == new_values.get('temp_high')].category.values[0] -
                       key[key['temp'] == new_values.get('temp_low')].category.values[0])))

    t.append(float(key[(key['rh'] == new_values.get('rh_low')) | (key['rh'] == new_values.get('rh_high'))].category.mean()))
    t.append(float(abs(key[key['rh'] == new_values.get('rh_high')].category.values[0] -
                       key[key['rh'] == new_values.get('rh_low')].category.values[0])))

    t.append(float(
        key[(key['water'] == new_values.get('water_low')) | (key['water'] == new_values.get('water_high'))].category.mean()))
    t.append(float(abs(key[key['water'] == new_values.get('water_high')].category.values[0] -
                       key[key['water'] == new_values.get('water_low')].category.values[0])))

    t.append(float(key[key['soil'] == 'Foliage plants'].category.values[0]))

    # cur.execute can only take 2 arguments so we need to add the ID to the list
    t.append(id)

    con = sql.connect('plant_requirements.db')
    cur = con.cursor()

    cur.execute('UPDATE requirements '
                'SET '
                'botanical_name = ?, '
                'common_name = ?, '
                'light_category = ?, '
                'light_tolerance = ?, '
                'temp_category = ?, '
                'temp_tolerance = ?, '
                'rh_category = ?, '
                'rh_tolerance = ?, '
                'water_category = ?, '
                'water_tolerance = ?, '
                'soil_category = ? '
                'WHERE ID = ?', t)

    con.commit()
    con.close()