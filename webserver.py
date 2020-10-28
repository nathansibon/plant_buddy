from flask import Flask, render_template, request, redirect, url_for
from forms import *
from lib_webserver import *
import csv, string, random
from os import path, chdir, getcwd
from pytz import all_timezones
from time import sleep
from configparser import ConfigParser

abspath = path.abspath(__file__)
dname = path.dirname(abspath)
chdir(dname)
cp = ConfigParser()
cp.read('config.ini')

app = Flask(__name__)  # application 'app' is object of class 'Flask'

letters = string.ascii_lowercase
app.config['SECRET_KEY'] = (''.join(random.choice(letters) for i in range(10)))

verify_db(cp['g']['plant_db_path'] + 'my_plants.db')
img_directory = 'my_plant_images'


# -----------------------------------------------------------------------------------------------------------#

# TODO add badge to "my plants" nav when plants need to be watered?

@app.route('/')  # root : main page
def index():
    f_name = cp['g']['name'].replace('_', ' ')
    f_location = cp['g']['location'].replace('_', ' ')

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

    return render_template('index.html', **data, s_temp=cp['g']['temp_humid'], s_light=cp['g']['light'],
                           s_soil=cp['g']['soil_moisture'])


@app.route('/test/', methods=['GET', 'POST'])
def test():
    return render_template('test.html')


@app.route('/my_plants/')
def my_plants():
    (columns, rows) = read_all('houseplants')
    for row in rows:
        print(row)
    plant_timeline(cp['g']['plant_db_path'] + 'my_plants.db', getcwd() + '/static/')
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
    (req, key, combined_name, soil_choice) = read_req_db()
    combined_name = ['none'] + combined_name

    form = NewPlant()
    form.species.choices = combined_name
    form.substrate.choices = soil_choice

    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        # since checkboxes do not return in POST objects if unchecked...
        print(len(result))
        if len(result) == 11:
            result[10] = 1
        else:
            result.append(0)
        print(result)
        uploaded_file = request.files['pic']
        if uploaded_file.filename != '':
            ext = os.path.splitext(uploaded_file.filename)[
                1]  # extract the file extension - this adds support for multiple image types (PNG, JPG, etc.)
            pic_save_path = getcwd() + '/static/' + 'plant_img_' + str(
                result[0] + ext)  # rename file based on unique plant name
            result.append('plant_img_' + result[0] + ext)  # add pic path to the database for later reference in html.
            result.append(1)  # change bool "has_pic" to true
            add_plant_to_database(result)
            uploaded_file.save(pic_save_path)
            img_resize(pic_save_path, 1000)  # resize image to max size, shortens load time when image is retrieved

        else:
            result.append('none')
            result.append(0)  # change bool "has_pic" to false
            add_plant_to_database(result)
        return redirect(url_for('my_plants'))

    return render_template('add_plant.html', form=form)


@app.route('/edit_plant/<id>', methods=['GET', 'POST'])
def edit_plant(id):
    print('id=' + str(id))
    (columns, row) = read_row(cp['g']['plant_db_path'] + 'my_plants.db', 'houseplants', 'ID', id)

    form = EditPlant(
        location=row[3],
        watering_schedule=row[6],
        last_watered=datetime.strptime(row[7], '%Y-%m-%d'),
        substrate=row[8],
        pot_size=row[9],
        leaf_temp_offset=row[10])

    (req, key, combined_name, soil_choice) = read_req_db()
    form.substrate.choices = soil_choice

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
            pic_save_path = getcwd() + '/static/' + 'plant_img_' + str(
                result[0] + ext)  # rename file based on unique plant name
            result.append('plant_img_' + row[1] + ext)  # add pic path to the database for later reference in html.
            result.append(1)  # change bool "has_pic" to true
            update_plant(id, result)
            uploaded_file.save(pic_save_path)
            img_resize(pic_save_path, 1000)  # resize image to max size, shortens load time when image is retrieved

        else:
            if plant_image_exists(row[1]):
                result.append(plant_image_exists(row[1]))
                result.append(1)  # keep bool "has_pic" to true
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

    (c, r) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db', 'select name from houseplants')
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
    (columns, rows) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db',
                               'select * from journal where plant="' + str(plant) + '"')
    for row in rows:
        print(row)
    return render_template('my_journal_filter.html', columns=columns, rows=rows)


@app.route('/add_journal/', methods=['GET', 'POST'])
def add_journal():
    (c, r) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db', 'select name from houseplants')
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
            ext = os.path.splitext(uploaded_file.filename)[
                1]  # extract the file extension - this adds support for multiple image types (PNG, JPG, etc.)
            pic_save_path = getcwd() + '/static/journal_img_' + str(
                result[0] + '_' + result[1] + ext)  # rename file based on journal date & title
            result.append(1)  # change bool "has_pic" to true
            result.append('journal_img_' + result[0] + '_' + result[
                1] + ext)  # add pic path to the database for later reference in html.
            add_journal_db(result)
            uploaded_file.save(pic_save_path)
            img_resize(pic_save_path, 1000)  # resize image to max size, shortens load time when image is retrieved

        else:
            result.append(0)  # change bool "has_pic" to false
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


# --------------------------------------------------------------------------------
# set of pages with resources info on plant care
@app.route('/resources_list_req/')
def resources_list_req():
    (columns, rows) = read_req()
    return render_template('resources_list_req.html', columns=columns, rows=rows)


@app.route('/resources_add_req_plant/', methods=['GET', 'POST'])
def resources_add_req_plant():
    form = ReqPlant()
    (req, key, combined_name, soil_choice) = read_req_db()

    form.light_low.choices = key.light.dropna().tolist()
    form.light_high.choices = key.light.dropna().tolist()
    form.temp_low.choices = key.temp.dropna().tolist()
    form.temp_high.choices = key.temp.dropna().tolist()
    form.rh_low.choices = key.rh.dropna().tolist()
    form.rh_high.choices = key.rh.dropna().tolist()
    form.water_low.choices = key.water.dropna().tolist()
    form.water_high.choices = key.water.dropna().tolist()
    form.soil_cat.choices = key.soil.dropna().tolist()

    if form.is_submitted():
        result = request.form.to_dict()
        add_req(result)
        return redirect(url_for('resources_list_req'))
    return render_template('resources_add_req_plant.html', form=form)


# TODO need to autopopulate fields with current value to avoid overwriting
'''
@app.route('/resources_edit_req/<id>', methods=['GET', 'POST'])
def resources_edit_req(id):
    print('id='+str(id))
    (columns, row) = read_row(cp['g']['plant_req_db_path'] + 'plant_requirements.db', 'requirements', 'ID', id)
    sub_row = {}
    for i in range(1,2):
        sub_row.update({columns[i] : row[i]})

    form = ReqPlant()
    (req, key, combined_name, soil_choice) = read_req_db()

    form.light_low.choices = key.light.dropna().tolist()
    form.light_high.choices = key.light.dropna().tolist()
    form.temp_low.choices = key.temp.dropna().tolist()
    form.temp_high.choices = key.temp.dropna().tolist()
    form.rh_low.choices = key.rh.dropna().tolist()
    form.rh_high.choices = key.rh.dropna().tolist()
    form.water_low.choices = key.water.dropna().tolist()
    form.water_high.choices = key.water.dropna().tolist()
    form.soil_cat.choices = key.soil.dropna().tolist()

    # TODO update to edit requirement, currently placeholder from edit plant
    if form.is_submitted():
        result = request.form.to_dict()
        print('form result:')
        print(result)
        update_req(id, key, result)
        return redirect(url_for('resources_list_req'))

    return render_template('resources_edit_req.html', form=form, id=id, row=row)
'''


# TODO finish soil
# might need to move to table in req database to allow user def soil mixes
@app.route('/resources_soil/')
def resources_soil():
    return render_template('temp.html')


# --------------------------------------------------------------------------------
# Set of pages for data query
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


@app.route('/data_location_select/', methods=['GET', 'POST'])
def data_location_select():
    form = GenSelect()

    (c, r) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db', 'select name from houseplants')
    plants_list = []
    for i in r:
        plants_list.append(i[0])
    print(plants_list)

    (c, r) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db', 'select name from other_locations')

    other_locations = []
    for i in r:
        other_locations.append(i[0])

    form.choice.choices = plants_list + other_locations

    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        print(result)
        plant = result[0]
        return redirect(url_for('data_location_display', plant=plant))

    return render_template('data_location_select.html', form=form)


@app.route('/data_location_display/<plant>')
def data_location_display(plant):
    # get plant info
    try:
        (c, p) = read_row(cp['g']['plant_db_path'] + 'my_plants.db', 'houseplants', 'ID', plant)
        print(p)
        is_plant = 1
        is_other = 0
    except:
        p = plant
        is_plant = 0
        is_other = 1

    # get sensor data
    try:
        data = get_all_plant_data(cp['g']['name'], plant)
    except Exception as e:
        print(e)
    print(data)

    return render_template('data_location_display.html', p=p, data=data, is_plant=is_plant, is_other=is_other)


@app.route('/data_charting_select/', methods=['GET', 'POST'])
def data_charting_select():
    return render_template('temp.html')


@app.route('/data_forecast/', methods=['GET', 'POST'])
def data_forecast():
    return render_template('temp.html')


@app.route('/settings_basic/', methods=['GET', 'POST'])
def settings_basic():
    form = SettingsBasic()
    current = [cp.get('g', field.name) for field in form if (field.name != 'csrf_token') and (field.name != 'submit')]
    form.timezone.choices = all_timezones  # from pytz module

    (c, r) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db', 'select name from houseplants')
    plants_list = []
    for i in r:
        plants_list.append(i[0])
    print(plants_list)

    (c, r) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db', 'select name from other_locations')

    other_locations = []
    for i in r:
        other_locations.append(i[0])

    form.location.choices = plants_list + other_locations

    form.timezone.data = cp.get('g', 'timezone')
    form.temp_scale.data = cp.get('g', 'temp_scale')
    form.location.data = cp.get('g', 'location')

    if form.is_submitted():
        print('Form submit')
        result = request.form.to_dict()
        print(result)
        try:
            for field in form:
                if (field.name != 'csrf_token') and (field.name != 'submit'):
                    print(field.name + ' : ' + result.get(field.name))
                    cp.set('g', field.name, result.get(field.name))
            with open('config.ini', 'w') as f:
                cp.write(f)
            print('Settings updated!')
        except Exception as e:
            print(e)
        return redirect(url_for('index'))

    return render_template('settings_basic.html', form=form, current=current)


@app.route('/settings_add_loc/', methods=['GET', 'POST'])
def settings_add_loc():
    print('-------Add New Non-plant Location-------')
    form = NewLocation()

    if form.is_submitted():
        print('Form submitted')
        result = request.form.to_dict()
        print(result['name'])
        sqlq = 'INSERT INTO other_locations (name) VALUES("' + result['name'] + '")'
        sql_exec(cp['g']['plant_db_path'] + 'my_plants.db', sqlq)  # note this function has err handler built in
        sleep(1)
        return redirect(url_for('settings_basic'))

    return render_template('settings_add_loc.html', form=form)


@app.route('/settings_advanced/', methods=['GET', 'POST'])
def settings_advanced():
    form = SettingsAdvanced()
    current = [cp.get('g', field.name) for field in form if (field.name != 'csrf_token') and (field.name != 'submit')]
    form.timezone.choices = all_timezones  # from pytz module

    (c, r) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db', 'select name from houseplants')
    plants_list = []
    for i in r:
        plants_list.append(i[0])
    print(plants_list)

    (c, r) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db', 'select name from other_locations')

    other_locations = []
    for i in r:
        other_locations.append(i[0])

    form.location.choices = plants_list + other_locations

    form.timezone.data = cp.get('g', 'timezone')
    form.temp_scale.data = cp.get('g', 'temp_scale')
    form.location.data = cp.get('g', 'location')
    form.temp_humid.data = cp.getboolean('g', 'temp_humid')
    form.light.data = cp.getboolean('g', 'light')
    form.soil_moisture.data = cp.getboolean('g', 'soil_moisture')

    if form.is_submitted():
        print('Form submit')
        result = request.form.to_dict()
        print(result)

        for i in ['temp_humid', 'light', 'soil_moisture']:
            result = eval_checkbox(i, result)
        print(result)

        try:
            for field in form:
                if (field.name != 'csrf_token') and (field.name != 'submit'):
                    print(field.name + ' : ' + result.get(field.name))
                    cp.set('g', field.name, result.get(field.name))
            with open('config.ini', 'w') as f:
                cp.write(f)
            print('Settings updated!')
        except Exception as e:
            print(e)
        return redirect(url_for('index'))

    return render_template('settings_advanced.html', form=form, current=current)


# Set of pages to read system logs
@app.route('/log_select/', methods=['GET', 'POST'])
def log_select():
    form = logSelect()
    form.log.choices = files_in_dir(dname + '/logs/')
    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        print(result)
        return redirect(url_for('log_result', file=result[0]))
    return render_template('log_select.html', form=form)


@app.route('/log_result/<file>', methods=['GET', 'POST'])
def log_result(file):
    result = read_log(dname + '/logs/' + file)
    return render_template('log_result.html', file=file, result=result)


@app.route('/log_clear/<file>', methods=['GET', 'POST'])
def log_clear(file):
    print('clearing log ' + str(file))
    clear_log(dname + '/logs/' + file)
    return redirect(url_for('log_result', file=file))


# -----------------------------------------------------------------------------------------------------------#


# this method sets the chart images, database queries, etc. to expire so the browser will fetch new data instead of using the cache
@app.after_request
def add_header(response):
    response.cache_control.max_age = 1
    response.cache_control.public = True
    return response


if __name__ == '__main__':
    # '0.0.0.0' = 127.0.0.1 i.e. localhost
    # port = 5000 : we can modify it for localhost
    app.run(host='0.0.0.0', port=5000, debug=True)  # local webserver : app.run()
