from flask import Flask, render_template, request, redirect, url_for
from forms import *
from os import path, chdir
from pathlib import Path
from lib_webserver import *
from config import *
import csv, os
from pytz import all_timezones
from time import sleep
from configparser import ConfigParser


abspath = path.abspath(__file__)
dname = path.dirname(abspath)
chdir(dname)

cp = ConfigParser()

#if not path.isfile('test_config.ini'):
    #init_config(cp)

cp.read('test_config.ini')

app = Flask(__name__) # application 'app' is object of class 'Flask'
app.config['SECRET_KEY'] = 'sparklingcider' #TODO change to random number
init_database('my_plants')
img_directory = 'my_plant_images'

#-----------------------------------------------------------------------------------------------------------#


@app.route('/', methods=['GET', 'POST'])  # root : main page
def index():

    f_name = name.replace('_', '')
    f_location = location.replace('_', '')

    data = {
        'name': f_name,
        'location': f_location
    }

    # Get the current status variables from CSV
    reader = csv.reader(open('webpage_sensor_data.csv'))
    for row in reader:
        if row[0] == '':
            pass
        else:
            data[row[0]] = row[1]

    # Get yesterday's variables from CSV
    reader = csv.reader(open('webpage_daily_data.csv'))
    for row in reader:
        if row[0] == '':
            pass
        else:
            data[row[0]] = row[1]

    # Get all-time variables from CSV
    reader = csv.reader(open('webpage_all_time_data.csv'))
    for row in reader:
        if row[0] == '':
            pass
        else:
            data[row[0]] = row[1]

    return render_template('index.html', **data)

@app.route('/test/')
def test():
    return render_template('test.html')


@app.route('/my_plants/')
def my_plants():
    (columns, rows) = read_all('houseplants')
    for row in rows:
        print(row)
    return render_template('my_plants.html', columns=columns, rows=rows)


@app.route('/my_plants_detailed/')
def my_plants_detailed():
    (columns, rows) = read_all('houseplants')
    return render_template('my_plants_detailed.html', columns=columns, rows=rows)


@app.route('/water_one_plant/<id>')
def water_one_plant(id):
    water_plant(id)
    sleep(1)
    return redirect(url_for('my_plants'))


@app.route('/water_all/')
def water_all():
    water_plant('all')
    sleep(1)
    return redirect(url_for('my_plants'))


@app.route('/add_plant/', methods=['GET', 'POST'])
def add_plant():
    form = NewPlant()
    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        print(result)
        uploaded_file = request.files['pic']
        if uploaded_file.filename != '':
            ext = os.path.splitext(uploaded_file.filename)[1]  # extract the file extension - this adds support for multiple image types (PNG, JPG, etc.)
            pic_save_path = Path.cwd() / 'static' / str('plant_img_' + result[0] + ext)  # rename file based on unique plant name
            result.append('plant_img_' + result[0] + ext)  # add pic path to the database for later reference in html.
            result.append(1)  # change bool "has_pic" to true
            add_plant_to_database(result)
            uploaded_file.save(pic_save_path)  # using python 3 Path to handle windows machines during code testing
        else:
            result.append('none')
            result.append(0) # change bool "has_pic" to false
            add_plant_to_database(result)
        return redirect(url_for('my_plants'))

    return render_template('add_plant.html', form=form)


@app.route('/edit_plant/<id>', methods=['GET', 'POST'])
def edit_plant(id):
    print('id='+str(id))
    (columns, row) = read_row('my_plants.db', 'houseplants', 'ID', id)

    form = EditPlant(
        location=row[1],
        watering_schedule=row[6],
        last_watered=datetime.strptime(row[7], '%Y-%m-%d'),
        substrate=row[8],
        pot_size=row[9],
        leaf_temp_offset=row[10])

    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        print(result)

        # check if the pot size changed, if so update the "last re-pot" date
        if result[4] != row[9]:  # items are 'pot_size' from form, and 'pot_size' from database
            result.append(date.today().strftime('%Y/%m/%d'))
        else:
            result.append(row[18])  # 'last_repot_date' from database

        # pic
        uploaded_file = request.files['pic']
        if uploaded_file.filename != '':
            # check if image already exists for this entry, if true delete existing image
            if plant_image_exists(result[0]) != False:
                    del_plant_image(result[0])

            # extract the file extension - this adds support for multiple image types (PNG, JPG, etc.)
            ext = os.path.splitext(uploaded_file.filename)[1]
            pic_save_path = Path.cwd() / 'static' / str('plant_img_' + row[1] + ext)  # rename file based on unique plant name
            result.append('plant_img_' + row[1] + ext)  # add pic path to the database for later reference in html.
            result.append(1)  # change bool "has_pic" to true
            update_plant(id, result)
            uploaded_file.save(pic_save_path)  # using python 3 Path to handle windows machines during code testing

        else:
            if plant_image_exists(row[1]):
                result.append(plant_image_exists(row[1]))
                result.append(1) # keep bool "has_pic" to true
            else:
                result.append('none')
                result.append(0)  # change bool "has_pic" to false
            update_plant(id, result)

        return redirect(url_for('my_plants'))

    return render_template('edit_plant.html', form=form, id=id, row=row)


@app.route('/del_my_plant/<id>/<p_name>')
def del_my_plant(id, p_name):
    del_plant(id)
    del_plant_image(p_name)
    sleep(1)
    return redirect(url_for('my_plants'))


@app.route('/my_journal/', methods=['GET', 'POST'])
def my_journal():
    (columns, rows) = read_all('journal')
    for row in rows:
        print(row)

    (c, r) = read_sql('my_plants.db', 'select name from houseplants')
    plants_list = ['--Filter Journals by Plant--', 'General']
    for i in r:
        plants_list.append(i[0])
    print(plants_list)

    form = FilterJournal()
    form.plant.choices = plants_list

    if request.method == 'POST':
        print('redirect to filter')
        result = get_form_data(list(request.form.values()))
        plant = result[0]

        if plant != '--Filter Journals by Plant--':
            return redirect(url_for('my_journal_filter', plant=plant))

    return render_template('my_journal.html', columns=columns, rows=rows, form=form)


@app.route('/my_journal_filter/<plant>')
def my_journal_filter(plant):
    (columns, rows) = read_sql('my_plants.db', 'select * from journal where plant="' + str(plant) + '"')
    for row in rows:
        print(row)
    return render_template('my_journal_filter.html', columns=columns, rows=rows)


@app.route('/add_journal/', methods=['GET', 'POST'])
def add_journal():
    (c, r) = read_sql('my_plants.db', 'select name from houseplants')
    plants_list = ['General']
    for i in r:
        plants_list.append(i[0])
    print(plants_list)
    form = NewJournal()
    form.plant.choices = plants_list

    if form.is_submitted():

        result = [datetime.today().strftime('%Y-%m-%d')]
        for i in get_form_data(list(request.form.values())):
            result.append(i)

        uploaded_file = request.files['pic']

        if uploaded_file.filename != '':
            ext = os.path.splitext(uploaded_file.filename)[1]  # extract the file extension - this adds support for multiple image types (PNG, JPG, etc.)
            pic_save_path = Path.cwd() / 'static' / str('journal_img_' + result[0] + '_' + result[1] + ext)  # rename file based on journal date & title
            result.append(1)  # change bool "has_pic" to true
            result.append('journal_img_' + result[0] + '_' + result[1] + ext)  # add pic path to the database for later reference in html.
            add_journal_db(result)
            uploaded_file.save(pic_save_path)  # using python 3 Path to handle windows machines during code testing
        else:
            result.append(0) # change bool "has_pic" to false
            result.append('none')
            add_journal_db(result)

        return redirect(url_for('my_journal'))

    return render_template('add_journal.html', form=form)


@app.route('/del_journal/<id>/<pic_name>')
def del_journal(id, pic_name):
    del_entry(id)
    if journal_image_exists(pic_name):
        del_journal_image(pic_name)
    sleep(1)
    return redirect(url_for('my_journal'))


@app.route('/list_req/')
def list_req():
    (columns, rows) = read_req()
    return render_template('list_req.html', columns=columns, rows=rows)


@app.route('/add_req_plant/', methods=['GET', 'POST'])
def add_req_plant():
    form = NewReqPlant()
    if form.is_submitted():
        result = request.form.to_dict()
        add_req(result)
        return redirect(url_for('list_req'))
    return render_template('add_req_plant.html', form=form)


@app.route('/edit_req/<id>', methods=['GET', 'POST'])
def edit_req(id):
    print('id='+str(id))
    (columns, row) = read_row('plant_requirements.db', 'requirements', 'ID', id)
    sub_row = {}
    for i in range(1,2):
        sub_row.update({columns[i] : row[i]})
    form = UpdateReqPlant()

    # TODO update to edit requirement, currently placeholder from edit plant
    if form.is_submitted():
        result = request.form.to_dict()
        print('form result:')
        print(result)
        #update_plant(id, result)
        return redirect(url_for('list_req'))

    return render_template('edit_req.html', form=form, id=id, row=row)

# Set of pages for general SQL query
@app.route('/sql_db_select/', methods=['GET', 'POST'])
def sql_db_select():
    form = sqlDBselect()
    form.database.choices = ['my_plants.db', 'plant_requirements.db', cp['g']['name'] + '_data.db']
    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        print(result)
        return redirect(url_for('sql_query', database=result[0]))
    return render_template('sql_db_select.html', form=form)


@app.route('/sql_query/<database>', methods=['GET', 'POST'])
def sql_query(database):
    print('query page')
    print(database)
    tables = get_db_tables(database)
    form = sqlQuery()
    if form.is_submitted():
        query = get_form_data(list(request.form.values()))[0]
        print(query)
        return redirect(url_for('sql_result', database=database, query=query))
    return render_template('sql_query.html', form=form, tables=tables)


@app.route('/sql_result/<database>/<query>')
def sql_result(database, query):
    print(database)
    print(query)
    (columns, rows) = read_sql(database, query)
    print(columns)
    print(rows)
    return render_template('sql_result.html', columns=columns, rows=rows, database=database, query=query)


# Set of pages for general SQL query
@app.route('/data_plant_select/', methods=['GET', 'POST'])
def data_plant_select():
    form = GenSelect()

    (c, r) = read_sql('my_plants.db', 'select name from houseplants')
    plants_list = []
    for i in r:
        plants_list.append(i[0])
    print(plants_list)
    form.choice.choices = plants_list

    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        print(result)
        plant = result[0]
        return redirect(url_for('data_plant_display', plant=plant))

    return render_template('data_plant_select.html', form=form)


@app.route('/data_plant_display/<plant>')
def data_plant_display(plant):

    # get plant info
    try:
        plant_id = read_sql('my_plants.db', 'select ID from houseplants where name="' + str(plant) + '"')
        plant_id = plant_id[1][0][0]
        print(plant_id)
        (c, p) = read_row('my_plants.db', 'houseplants', 'ID', plant_id)
        print(p)
    except Exception as e:
        print(e)
        p= ['','Error: No plant found :(']
        for i in range(16):
            p.append('')

    # get sensor data
    try:
        data = get_all_plant_data(cp['g']['name'], plant)
    except:
        cols = ['drybulb', 'rh', 'vpd', 'lux']
        var_type = ['_mean', '_max', '_min', '_q_90', '_q_10']
        data = {}
        for i in cols:
            for j in var_type:
                data[str(i+j)] = 'n-a'
    print(data)

    return render_template('data_plant_display.html', p=p, data=data)


@app.route('/data_charting_select/', methods=['GET', 'POST'])
def data_charting_select():

    return render_template('sql_db_select.html')


@app.route('/settings_basic/', methods=['GET', 'POST'])
def settings_basic():

    form = SettingsBasic()
    current = [cp.get('g', field.name) for field in form if (field.name != 'csrf_token') and (field.name != 'submit')]
    form.timezone.choices = all_timezones # from pytz module

    (c, r) = read_sql('my_plants.db', 'select name from houseplants')
    plants_list = []
    for i in r:
        plants_list.append(i[0])
    print(plants_list)
    form.location.choices = plants_list

    form.timezone.data = cp.get('g', 'timezone')
    form.temp_scale.data = cp.get('g', 'temp_scale')
    form.location.data = cp.get('g', 'location')

    if form.is_submitted():
        result = request.form.to_dict()
        print(result)
        try:
            for field in form:
                if (field.name != 'csrf_token') and (field.name != 'submit'):
                    print(field.name + ' : ' + result.get(field.name))
                    cp.set('g', field.name, result.get(field.name))
            with open('test_config.ini', 'w') as f:
                cp.write(f)
            print('Settings updated!')
        except Exception as e:
            print(e)
        return redirect(url_for('index'))

    return render_template('settings_basic.html', form=form, current=current)

# todo update code after form submission
@app.route('/settings_advanced/', methods=['GET', 'POST'])
def settings_advanced():

    form = SettingsAdvanced()
    current = [cp.get('g', field.name) for field in form if (field.name != 'csrf_token') and (field.name != 'submit')]
    form.timezone.choices = all_timezones # from pytz module
    (c, r) = read_sql('my_plants.db', 'select name from houseplants')
    plants_list = []
    for i in r:
        plants_list.append(i[0])
    print(plants_list)
    form.location.choices = plants_list

    form.timezone.data = cp.get('g', 'timezone')
    form.temp_scale.data = cp.get('g', 'temp_scale')
    form.location.data = cp.get('g', 'location')
    form.temp_humid.data = cp.getboolean('g', 'temp_humid')
    form.light.data = cp.getboolean('g', 'light')
    form.soil_moisture.data = cp.getboolean('g', 'soil_moisture')

    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        print(result)

        return #redirect(url_for('index'))

    return render_template('settings_advanced.html', form=form, current=current)

#-----------------------------------------------------------------------------------------------------------#


# this method sets the chart images, database queries, etc. to expire so the browser will fetch new data instead of using the cache
@app.after_request
def add_header(response):
    response.cache_control.max_age = 1
    response.cache_control.public = True
    return response

if __name__ == '__main__':
    # '0.0.0.0' = 127.0.0.1 i.e. localhost
    # port = 5000 : we can modify it for localhost
    app.run(port=5000, debug=True) # local webserver : app.run()