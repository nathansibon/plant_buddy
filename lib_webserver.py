import sqlite3 as sql
import pandas as pd
import numpy as np
import os, sys_var
from os.path import isfile, join
from datetime import date, datetime, timedelta
from pathlib import Path
from configparser import ConfigParser
from PIL import Image
import matplotlib
import matplotlib.pyplot as plt

cp = ConfigParser()
cp.read('config.ini')

# set matplotlib to "backend mode" to avoid multi-threadding errors
# https://github.com/matplotlib/matplotlib/issues/14304/
matplotlib.use('agg')


# read requirements database to feed into functions below
def read_req_db():
    db = cp['g']['plant_req_db_path'] + 'plant_requirements.db'
    print(db)
    con = sql.connect(db)

    req = pd.read_sql_query('SELECT * FROM requirements ORDER BY "botanical_name"', con)
    key = pd.read_sql_query('SELECT * FROM key', con)
    combined_name = (req['botanical_name'] + ' (' + req['common_name'] + ')').tolist()
    print(req.head())
    soil_choice = (key['soil']).tolist()

    return (req, key, combined_name, soil_choice)


# specific functions for webpages
def get_form_data(in_list):
    output = []
    print(in_list)
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


def eval_checkbox(name, result):
    # DOM, wtforms, and Configparser don't play nicely together with checkboxes... this fixes those issues...
    if isinstance(result, dict):
        if isinstance(name, str):
            if name in result:
                result[name] = '1'
            else:
                result[name] = '0'
            return result
        else:
            raise Exception('Error: 1st arg must be a string')
    else:
        raise Exception('Error: 2nd arg must be a dictionary')

    return result


def init_database(database):
    con = sql.connect(str(database) + '.db')

    # create table houseplants
    con.execute('CREATE TABLE IF NOT EXISTS houseplants ('
                'ID INTEGER PRIMARY KEY AUTOINCREMENT,'  # 0
                'name varchar(765),'  # 1
                'species varchar(765),'  # 2
                'location varchar(765),'  # 3
                'purchased_from varchar(765),'  # 4
                'purchase_date timestamp,'  # 5
                'water_schedule_in_days integer,'  # 6
                'last_watered timestamp,'  # 7
                'substrate varchar(765),'  # 8
                'pot_size real,'  # 9
                'leaf_temp_offset integer,'  # 10
                'pic_path varchar(765),'  # 11
                'has_pic smallint,'  # 12
                'days_since_last_water integer,'  # 13
                'need_water smallint,'  # 14
                'water_warning smallint,'  # 15
                'ignore smallint,'  # 16
                'death smallint,'  # 17
                'last_repot_date timestamp)')  # 18

    # create table my_journal
    con.execute('CREATE TABLE IF NOT EXISTS journal ('
                'ID INTEGER PRIMARY KEY AUTOINCREMENT,'  # 0
                'date timestamp, '  # 1
                'title varchar(765),'  # 2
                'plant varchar(765),'  # 3
                'body text,'  # 4
                'has_pic smallint,'  # 5
                'pic_path varchar(765))')  # 6

    # create table other_locations
    con.execute('CREATE TABLE IF NOT EXISTS other_locations ('
                'ID INTEGER PRIMARY KEY AUTOINCREMENT,'  # 0
                'name varchar(765))')  # 1

    con.execute('INSERT OR REPLACE INTO other_locations (ID, name) VALUES("1", "other")')
    con.commit()

    con.close()


def verify_db(database):
    print('-------Start verify db-------')
    database = str(database)
    print(database)

    con = sql.connect(database)
    cur = con.cursor()

    print('--Checking Tables--')
    for table in sys_var.check_webserver:
        print(table)
        con.execute('create table if not exists ' + str(table) + '(id integer primary key)')
        con.commit()

    tables = pd.read_sql_query("SELECT `name` FROM `sqlite_master` WHERE type='table'", con)
    print(tables)

    print('--Checking Columns--')
    for tbl in sys_var.check_webserver:
        if tbl in tables.name.values:
            columns = pd.read_sql_query("PRAGMA table_info('" + tbl + "')", con)
            for col in sys_var.check_webserver.get(tbl):
                if col[0] in columns.name.values:
                    pass
                elif col[0] == 'index':
                    pass
                else:
                    print('Table ' + tbl + ' missing column ' + col[0] + ', adding to db')
                    con.execute('ALTER TABLE ' + str(tbl) + ' ADD COLUMN ' + str(col[0]) + ' ' + col[1])
                    con.commit()
                    print()
        else:
            print('missing table: ' + tbl)
            q = 'create table if not exists ' + tbl + ' ('
            for i, txt in enumerate(sys_var.check_webserver.get(tbl)):
                if i == len(sys_var.check_datalogger.get(tbl)) - 1:
                    q = q + txt[0] + ' ' + txt[1]
                else:
                    q = q + txt[0] + ' ' + txt[1] + ', '
            q = q + ')'
            con.execute(q)
            con.commit()
            print()

    con.execute('INSERT OR REPLACE INTO other_locations (ID, name) VALUES("1", "other")')
    con.commit()

    con.close()
    print(database + ' verified')


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

    cur.execute('PRAGMA table_info(' + table + ')')
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

    return (columns, row[
        0])  # need to do row[0] instead of just row since the cursor returns a tuple of lists (we just need the list)


def read_sql(database, query):
    print('--------Start Database Query--------')
    print('Query:' + query)
    query = query.lower()
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


def sql_exec(database, query):
    print('--------Start Database Exec--------')
    print('Query:' + query)
    database = str(database)
    print(database)

    con = sql.connect(database)
    cur = con.cursor()

    try:
        con.execute(query)
        con.commit()
        result = 1
    except Exception as e:
        result = 0
        print(e)

    return result


def read_all(table):
    print('----Starting read all----')
    con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
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


def add_new_plant(result):

    print('----Starting add plant to db----')

    # add last plant vars
    result['ignore'] = 0
    result['need_water'] = 0
    result['water_warning'] = 0
    result['death'] = 0
    result['sold'] = 0
    result['days_since_last_water'] = pd.Timestamp.now() - pd.Timestamp(result.get('last_watered'))
    result['last_repot_date'] = date.today().strftime('%Y/%m/%d')

    print(type(result.get('water_schedule_in_days')))

    if result.get('days_since_last_water') >= pd.Timedelta(result.get('water_schedule_in_days') + ' days'):
        result['need_water'] = 1
    elif pd.Timedelta(str(result.get('water_schedule_in_days')) + ' days') - result.get('days_since_last_water') < pd.Timedelta('3 days'):
        result['water_warning'] = 1  # if less than 3 days until needs water, set warning to True
    result['days_since_last_water'] = result.get('days_since_last_water').days  # set days_since_last_water back to integer from Pandas Timedelta

    print(result)
    sql_insert(cp['g']['plant_db_path'] + 'my_plants.db', 'houseplants', result)
    update_global()


def update_plant(id, result):
    print('----Starting update plant----')
    print(result)
    print(type(result))
    print(type(result.get('last_watered')))

    result['days_since_last_water'] = pd.Timestamp.now() - pd.Timestamp(result.get('last_watered'))  # days_since_last_water
    result['need_water'] = 0
    result['water_warning'] = 0
    print(result.get('need_water'))

    if result.get('days_since_last_water') >= pd.Timedelta(result.get('water_schedule_in_days') + ' days'):  # days_since_last_water > water_schedule_in_days
        result['need_water'] = 1
    elif pd.Timedelta(result.get('water_schedule_in_days') + ' days') - result.get('days_since_last_water') < pd.Timedelta('3 days'):
        result['water_warning'] = 1  # if less than 3 days until needs water, set warning to True
    result['days_since_last_water'] = result.get('days_since_last_water').days  # set days_since_last_water back to integer from Pandas Timestamp

    print(result)
    sql_update(cp['g']['plant_db_path'] + 'my_plants.db', 'houseplants', result, 'id', id)
    update_global()


def del_plant(id):
    print('----Deleting plant----')
    print('id = ' + str(id))

    con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
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
    cols = ['drybulb', 'rh', 'vpd', 'lux']

    con = sql.connect(database + '_data.db')

    q = 'SELECT * FROM indoor_raw WHERE location="' + str(plant) + '"'
    print(q)
    raw_data = pd.read_sql_query(q, con)
    print(raw_data)
    result = {}

    for i in cols:
        result[str(i + '_mean')] = np.round(raw_data[i].mean(), 1)
        result[str(i + '_max')] = np.round(raw_data[i].max(), 1)
        result[str(i + '_min')] = np.round(raw_data[i].min(), 1)
        result[str(i + '_q_10')] = np.round(raw_data[i].quantile(0.1), 1)
        result[str(i + '_q_90')] = np.round(raw_data[i].quantile(0.9), 1)
    result['count'] = raw_data['location'].count()

    return result


def plant_watering_week():

    current = datetime.now().date()

    day_names = {}
    days = {}

    for i in range(0, 8):
        days[str(i)] = []
        day_names[str(i)] = (current + timedelta(days=i)).strftime('%A')
    print(days)

    con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
    cur = con.cursor()

    cur.execute(
        'SELECT id, name, water_schedule_in_days, last_watered, days_since_last_water FROM houseplants WHERE ignore = 0'
    )
    # sort plants into next 7 days of watering
    for i in cur:
        if i[2] - i[4] < 0:
            days['0'].append(i[1])
        elif i[2] - i[4] > 7:
            pass
        else:
            days[str(i[2] - i[4])].append(i[1])  # water_schedule_in_days - days_since_last_water, name

    print(days)
    ''' USE THIS TO ITERATE THROUGH RETURNED DICT
    for key in days:
        print(key)
        for plant in days[key]:
            print(plant)
    '''
    return days, day_names


def plant_overview_charts(database, static_path):
    con = sql.connect(database)

    p = pd.read_sql_query('select * from houseplants', con)

    print(p.columns)

    # --------- Plant Timeline ---------
    p['count'] = 1
    p['cum'] = p.sort_values('purchase_date')['count'].cumsum()
    sub = p[['purchase_date', 'cum', 'name']].sort_values('purchase_date')
    print(sub)

    # thanks to https://matplotlib.org/3.2.1/gallery/lines_bars_and_markers/timeline.html
    # Choose some nice levels
    levels = np.tile([-5, 5, -3, 3, -1, 1],
                     int(np.ceil(len(sub['purchase_date']) / 6)))[:len(sub['purchase_date'])]

    # Create figure and plot a stem plot with the date
    fig, ax = plt.subplots(constrained_layout=True, figsize=(10, 5))
    ax.set(title='Plant Family Timeline')

    markerline, stemline, baseline = ax.stem(sub['purchase_date'], levels,
                                             linefmt="blue", basefmt="k-")  # ,use_line_collection=True)

    plt.setp(markerline, mec="k", mfc="w", zorder=3)

    # Shift the markers to the baseline by replacing the y-data by zeros.
    markerline.set_ydata(np.zeros(len(sub['purchase_date'])))

    # annotate lines
    vert = np.array(['top', 'bottom'])[(levels > 0).astype(int)]
    for d, l, r, va in zip(sub['purchase_date'], levels, sub['name'], vert):
        ax.annotate(r, xy=(d, l), xytext=(-3, np.sign(l) * 3),
                    textcoords="offset points", va=va, ha="right")

    # remove y axis and spines
    ax.get_yaxis().set_visible(False)
    for spine in ["left", "top", "right"]:
        ax.spines[spine].set_visible(False)

    ax.margins(y=0.1)
    plt.xticks(rotation=45)
    plt.savefig(static_path + 'my_plants_timeline.png', format='png', dpi=200)

    # --------- Plant Location Counts ---------
    d = p['location'].value_counts()
    print(d.index.values)
    print(d.values)

    new_labels = [i.replace(' ', '\n') for i, j in d.iteritems()]

    fig, axs = plt.subplots(figsize=(8, 4))
    axs.bar(new_labels, d.values)
    fig.suptitle('Plant Locations')
    plt.tight_layout()
    plt.savefig(static_path + 'my_plants_location.png', format='png', dpi=200)

    # --------- Plant Watering Schedules ---------
    d = p['water_schedule_in_days'].value_counts()
    print(d.index.values)
    print(d.values)

    fig, axs = plt.subplots(figsize=(8, 4))
    axs.bar(d.index.values, d.values)
    fig.suptitle('Plant Watering Schedules (days)')
    plt.savefig(static_path + 'my_plants_water_schedule.png', format='png', dpi=200)

    # --------- Plant Pot Sizes ---------
    d = p['pot_size'].value_counts()
    print(d.index.values)
    print(d.values)

    fig, axs = plt.subplots(figsize=(8, 4))
    axs.bar(d.index.values, d.values)
    fig.suptitle('Plant Pot Sizes (in)')
    plt.savefig(static_path + 'my_plants_pot_size.png', format='png', dpi=200)

    # --------- Plant Purchase Locations ---------
    d = p['purchased_from'].value_counts()
    print(d.index.values)
    print(d.values)

    new_labels = [i.replace(' ', '\n') for i, j in d.iteritems()]

    fig, axs = plt.subplots(figsize=(8, 5))
    axs.bar(new_labels, d.values)
    fig.suptitle('Plants Purchased From')
    plt.tight_layout()
    plt.savefig(static_path + 'my_plants_purchased_from.png', format='png', dpi=200)


def update_global():
    # update plants_to_water global variable
    print('-----------------Updating Global-----------------')
    con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
    cur = con.cursor()
    cur.execute('select count(*) from houseplants where need_water="1" OR water_warning="1"')
    count = cur.fetchone()
    print('plants_to_water = ' + str(count[0]))
    cp.set('water', 'plants_to_water', str(count[0]))
    with open('config.ini', 'w') as f:
        cp.write(f)


def update_water():
    print('-----------Start Update Water-----------')
    current = datetime.now().date()
    con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
    cur = con.cursor()

    cur.execute(
        'SELECT id, ' \
        'name, ' \
        'water_schedule_in_days, ' \
        'last_watered, '
        'days_since_last_water, ' \
        'water_warning, ' \
        'need_water ' \
        'FROM houseplants WHERE ignore = 0'
    )

    print('name, water warning, need water, days_since_last_water, schedule - last water <=2, last water > schedule')
    for i in cur:
        days_since_last_water = (current - datetime.strptime(i[3], '%Y-%m-%d').date()).days
        print(i[1], i[5], i[6], days_since_last_water, i[2] - i[4] <= 2, i[4] > i[2])
        # name, water warning, need water, XX, schedule - last water <=2, last water > schedule

        if days_since_last_water >= i[2]:
            print('time to water ' + i[1])
            con.execute('UPDATE houseplants SET need_water = 1, water_warning = 0 WHERE id = "' + str(i[0]) + '"')
            con.commit()
        elif i[2] - i[4] <= 2:
            print('2 days to water ' + i[1])
            con.execute('UPDATE houseplants SET water_warning = 1, need_water = 0 WHERE id = "' + str(i[0]) + '"')
            con.commit()

        con.execute(
            'UPDATE houseplants SET days_since_last_water = ' + str(days_since_last_water) + ' WHERE id = "' + str(
                i[0]) + '"')
        con.commit()

    update_global()

    con.close()
    print('-----------End Update Water-----------')


def water_plant(id):
    print('----Starting water plant----')

    con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
    cur = con.cursor()

    if id == 'all':
        print('water all')
        cur.execute('SELECT ID FROM houseplants')
        ids = cur.fetchall()  # recall fetch annoyingly returns a list of tuples, so we need to access the tuple item to get the raw value...

        for item in ids:
            print(item[0])
            cur.execute('UPDATE houseplants SET '
                        'last_watered = ?, '
                        'need_water = ?, '
                        'water_warning = ?, '
                        'days_since_last_water = ? '
                        'WHERE ID = ?',
                        [datetime.today().strftime('%Y-%m-%d'), 0, 0, 0, item[0]])
    else:
        print('water one, id= ' + str(id))
        cur.execute('UPDATE houseplants SET '
                    'last_watered = ?, '
                    'need_water = ?, '
                    'water_warning = ?, '
                    'days_since_last_water = ? '
                    'WHERE ID = ?',
                    [datetime.today().strftime('%Y-%m-%d'), 0, 0, 0, id])

    con.commit()
    con.close()
    update_global()


def set_plant_ignore(id, current):
    print('----Starting plant ignore----')

    print('Current: ' + current)
    val = 1 - int(current)  # swaps between 0 and 1

    con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
    cur = con.cursor()

    print('plant death, id= ' + str(id))
    cur.execute('UPDATE houseplants SET ignore = ? WHERE ID = ?', [val, id])
    con.commit()
    con.close()


def set_plant_death(id):
    print('----Starting plant death----')

    con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
    cur = con.cursor()

    print('plant death, id= ' + str(id))
    cur.execute('UPDATE houseplants SET death = ? WHERE ID = ?', [1, id])
    con.commit()
    con.close()


def set_plant_sold(id):
    print('----Starting plant sold----')

    con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
    cur = con.cursor()

    print('plant sold, id= ' + str(id))
    cur.execute('UPDATE houseplants SET sold = ? WHERE ID = ?', [1, id])
    con.commit()
    con.close()


def del_entry(id):
    print('----Deleting Journal Entry----')
    print('id = ' + str(id))

    con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
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

    con = sql.connect(cp['g']['plant_req_db_path'] + 'plant_requirements.db')
    cur = con.cursor()

    cur.execute('PRAGMA table_info(requirements)')
    columns = cur.fetchall()
    print(columns[1])

    # returns a tuple of table names in this database
    cur.execute('SELECT * FROM requirements ORDER BY "botanical_name"')

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
        con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
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
    (req, key, combined_name, soil_choice) = read_req_db()

    print('start conversion')
    print(result)
    # process input from webpage - convert text descriptions to numeric keys and calculate tolerances
    t = {'botanical_name': result.get('botanical_name'), 'common_name': result.get('common_name')}

    t['light_category'] = float(key[(key['light'] == result.get('light_low')) | (key['light'] == result.get('light_high'))].category.mean())
    t['light_tolerance'] = float(abs(key[key['light'] == result.get('light_high')].category.values[0] - key[key['light'] == result.get('light_low')].category.values[0]))

    t['temp_category'] = float(key[(key['temp'] == result.get('temp_low')) | (key['temp'] == result.get('temp_high'))].category.mean())
    t['temp_tolerance'] = float(abs(key[key['temp'] == result.get('temp_high')].category.values[0] - key[key['temp'] == result.get('temp_low')].category.values[0]))

    t['rh_category'] = float(key[(key['rh'] == result.get('rh_low')) | (key['rh'] == result.get('rh_high'))].category.mean())
    t['rh_tolerance'] = float(abs(key[key['rh'] == result.get('rh_high')].category.values[0] - key[key['rh'] == result.get('rh_low')].category.values[0]))

    t['water_category'] = float(key[(key['water'] == result.get('water_low')) | (key['water'] == result.get('water_high'))].category.mean())
    t['water_tolerance'] = float(abs(key[key['water'] == result.get('water_high')].category.values[0] - key[key['water'] == result.get('water_low')].category.values[0]))

    t['soil_category'] = float(key[key['soil'] == 'Foliage plants'].category.values[0])

    sql_insert(cp['g']['plant_req_db_path'] + 'plant_requirements.db', 'requirements', t)


def update_req(id, key, new_values):
    # todo test updated sql functions
    print('----Starting read requirement----')
    print('start conversion')
    print(new_values)

    # process input from webpage - convert text descriptions to numeric keys and calculate tolerances
    t = {}

    t['light_category'] = float(key[(key['light'] == new_values.get('light_low')) | (key['light'] == new_values.get('light_high'))].category.mean())
    t['light_tolerance'] = float(abs(key[key['light'] == new_values.get('light_high')].category.values[0] - key[key['light'] == new_values.get('light_low')].category.values[0]))

    t['temp_category'] = float(key[(key['temp'] == new_values.get('temp_low')) | (key['temp'] == new_values.get('temp_high'))].category.mean())
    t['temp_tolerance'] = float(abs(key[key['temp'] == new_values.get('temp_high')].category.values[0] - key[key['temp'] == new_values.get('temp_low')].category.values[0]))

    t['rh_category'] = float(key[(key['rh'] == new_values.get('rh_low')) | (key['rh'] == new_values.get('rh_high'))].category.mean())
    t['rh_tolerance'] = float(abs(key[key['rh'] == new_values.get('rh_high')].category.values[0] - key[key['rh'] == new_values.get('rh_low')].category.values[0]))

    t['water_category'] = float(key[(key['water'] == new_values.get('water_low')) | (key['water'] == new_values.get('water_high'))].category.mean())
    t['water_tolerance'] = float(abs(key[key['water'] == new_values.get('water_high')].category.values[0] - key[key['water'] == new_values.get('water_low')].category.values[0]))

    t['soil_category'] = float(key[key['soil'] == 'Foliage plants'].category.values[0])

    sql_update(cp['g']['plant_req_db_path'] + 'plant_requirements.db', 'requirements', id, t)


def img_resize(infile, max_size):
    size = max_size, max_size
    im = Image.open(infile)

    # the thumbnail function will unfortunately strip out EXIF (including image orientation)
    # so we break it out first to preserve it.
    exif = im.info['exif']
    im.thumbnail(size)
    im.save(infile, exif=exif)


def files_in_dir(path):
    onlyfiles = [f for f in os.listdir(path) if isfile(join(path, f))]
    return onlyfiles


def read_log(f_abs_path):
    with open(f_abs_path, 'r') as f:
        lines = f.readlines()
    return lines


def clear_log(f_abs_path):
    with open(f_abs_path, 'w') as f:
        pass


def fix_null_col(database, table, col, value, val_type):
    con = sql.connect(database)
    cur = con.cursor()
    if val_type == 'str':
        q = 'update ' + table + ' set ' + col + ' = "' + value + '" where ' + col + ' is null'
    if val_type == 'int':
        q = 'update ' + table + ' set ' + col + ' = ' + value + ' where ' + col + ' is null'
    print(q)
    cur.execute(q)
    con.commit()
    con.close()


def sql_insert(database, table, new_values):
    # inserts new entry into a database
    # new_values should be a dictionary with keys matching column names
    con = sql.connect(database)
    # build query into a single string
    q = 'INSERT INTO ' + table + '('
    values = []
    for key in new_values:
        q = q + key + ', '
        values.append(new_values[key])
    q = q[: -2]  # remove last 2 characters, which at this point are unnecessary comma & space from the last loop
    print(q)
    q = q + ') VALUES ('
    for i in range(len(values)):
        q = q + '?, '
    q = q[: -2]
    q = q + ')'
    print(q)
    print(values)
    con.execute(q, values)
    con.commit()
    con.close()


def sql_update(database, table, new_values, id_name, id):
    # updates all columns for a single entry
    # new_values should be a dictionary with keys matching column names
    con = sql.connect(database)
    for key in new_values:
        print('update ' + table + ' set ' + key + ' = ' + str(new_values[key]) + ' where ' + id_name + ' = ' + id)
        con.execute('update ' + table + ' set ' + key + ' = "' + str(new_values[key]) + '" where ' + id_name + ' = ' + id)
        con.commit()
    con.close()