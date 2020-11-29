import csv
import random
import string
from configparser import ConfigParser
from os import path, chdir, getcwd
from time import sleep

from flask import Flask, render_template, request, redirect, url_for
from pytz import all_timezones

from forms import *
from lib_webserver import *

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
                           s_soil=cp['g']['soil_moisture'], ideal_vpd=cp['g']['ideal_vpd'], plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/test/', methods=['GET', 'POST'])
def test():
    form = NewJournal()
    if form.is_submitted():  # request.method == 'POST':
        if request.files:
            print('files:')
            pic = request.files['pic']
            if pic.filename != '':
                print(pic.filename)
        result = request.form.to_dict()
        print('result:')
        for i in result:
            print(i)
    return render_template('test.html', form=form, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/my_plants/')
def my_plants():
    (c, r) = read_sql(
        cp['g']['plant_db_path'] + 'my_plants.db',
        'SELECT * FROM houseplants WHERE death != 1 and sold != 1 ORDER BY need_water DESC, water_warning DESC'
    )
    (days, day_names) = plant_watering_week()

    for row in r:
        print(row)
    return render_template('my_plants.html', columns=c, rows=r, title='', days=days, day_names=day_names, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/my_plants_detailed/')
def my_plants_detailed():
    (columns, rows) = read_all('houseplants')
    return render_template('my_plants_detailed.html', columns=columns, rows=rows, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/plant_death/<id>')
def plant_death(id):
    set_plant_death(id)
    sleep(1)
    return redirect(url_for('my_plants'))


@app.route('/plant_sold/<id>')
def plant_sold(id):
    set_plant_sold(id)
    sleep(1)
    return redirect(url_for('my_plants'))


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


@app.route('/my_plants_graveyard/')
def my_plants_graveyard():
    (c, r) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db', 'SELECT * FROM houseplants WHERE death = 1')

    for row in r:
        print(row)
    return render_template('my_plants.html', columns=c, rows=r, title='☠ Plant Graveyard ☠', plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/my_plants_sold/')
def my_plants_sold():
    (c, r) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db', 'SELECT * FROM houseplants WHERE sold = 1')

    for row in r:
        print(row)
    return render_template('my_plants.html', columns=c, rows=r, title='$ Sold Plants $', plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/add_plant/', methods=['GET', 'POST'])
def add_plant():
    (req, key, combined_name, soil_choice) = read_req_db()
    combined_name = ['none'] + combined_name

    form = NewPlant()
    form.species.choices = combined_name
    form.substrate.choices = soil_choice

    if form.is_submitted():
        result = request.form.to_dict()
        result.pop('submit')
        print(result)
        if 'pic' in request.files:
            if request.files['pic'] != '':
                uploaded_file = request.files['pic']
                ext = os.path.splitext(uploaded_file.filename)[
                    1]  # extract the file extension - this adds support for multiple image types (PNG, JPG, etc.)
                pic_save_path = getcwd() + '/static/' + 'plant_img_' + str(
                    result.get('name') + ext)  # rename file based on unique plant name
                result['pic_path'] = ('plant_img_' + result.get('name') + ext)  # add pic path to the database for later reference in html.
                result['has_pic'] = 1  # change bool "has_pic" to true
                add_new_plant(result)
                uploaded_file.save(pic_save_path)
                img_resize(pic_save_path, 1000)  # resize image to max size, shortens load time when image is retrieved

        else:
            result.pop('pic')
            result['pic_path'] = 'none'
            result['has_pic'] = 0  # change bool "has_pic" to false
            add_new_plant(result)
        return redirect(url_for('my_plants'))

    return render_template('add_plant.html', form=form, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/edit_plant/<id>', methods=['GET', 'POST'])
def edit_plant(id):
    print('id=' + str(id))
    (columns, row) = read_row(cp['g']['plant_db_path'] + 'my_plants.db', 'houseplants', 'ID', id)

    print(row[6])

    form = EditPlant(
        species=row[2],
        location=row[3],
        purchased_from=row[4],
        water_schedule_in_days=row[6],
        last_watered=datetime.strptime(row[7], '%Y-%m-%d'),
        substrate=row[8],
        pot_size=row[9],
        leaf_temp_offset=row[10])

    (req, key, combined_name, soil_choice) = read_req_db()
    form.substrate.choices = soil_choice
    form.species.choices = combined_name

    if form.is_submitted():
        # todo something here is broken - check image upload, also watering scheudle does not populate
        result = request.form.to_dict()
        result.pop('submit')
        print(result)

        # check if the pot size changed, if so update the "last re-pot" date
        if result.get('pot_size') != row[9]:  # items are 'pot_size' from form, and 'pot_size' from database
            result['last_repot_date'] = date.today().strftime('%Y/%m/%d')
        else:
            result['last_repot_date'] = row[18]  # 'last_repot_date' from database

        # pic
        if 'pic' in request.files:
            if request.files['pic'] != '':
                uploaded_file = request.files['pic']
                print('pic found, check for existing image')
                # check if image already exists for this entry, if true delete existing image
                if plant_image_exists(row[1]) != False:
                    del_plant_image(row[1])
                    print('existing image deleted')

                # extract the file extension - this adds support for multiple image types (PNG, JPG, etc.)
                ext = os.path.splitext(uploaded_file.filename)[1]
                pic_save_path = getcwd() + '/static/' + 'plant_img_' + row[1] + ext  # rename file based on unique plant name
                result['pic_path'] = 'plant_img_' + row[1] + ext  # add pic path to the database for later reference in html.
                result['has_pic'] = 1  # change bool "has_pic" to true
                update_plant(id, result)
                uploaded_file.save(pic_save_path)
                img_resize(pic_save_path, 1000)  # resize image to max size, shortens load time when image is retrieved

        else:
            '''
            if plant_image_exists(row[1]):
                result['pic_path'] = plant_image_exists(row[1])
                # since has_pic is already true, no need to update
            else:
                result['pic_path'] = 'none'
                result['has_pic'] = 0  # change bool "has_pic" to false
            '''
            result.pop('pic')
            update_plant(id, result)

        return redirect(url_for('my_plants'))

    return render_template('edit_plant.html', form=form, id=id, row=row, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/ignore_my_plant/<id>/<current>')
def ignore_my_plant(id, current):
    set_plant_ignore(id, current)
    sleep(1)
    return redirect(url_for('my_plants'))


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

    return render_template('my_journal.html', columns=columns, rows=rows, form=form, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/my_journal_filter/<plant>')
def my_journal_filter(plant):
    (columns, rows) = read_sql(cp['g']['plant_db_path'] + 'my_plants.db',
                               'select * from journal where plant="' + str(plant) + '"')
    for row in rows:
        print(row)
    return render_template('my_journal_filter.html', columns=columns, rows=rows, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/add_journal/', methods=['GET', 'POST'])
def add_journal():
    # TODO update per new sql functions
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

    return render_template('add_journal.html', form=form, plants_to_water=int(cp['water']['plants_to_water']))


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
    return render_template('resources_list_req.html', columns=columns, rows=rows, plants_to_water=int(cp['water']['plants_to_water']))


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
    return render_template('resources_add_req_plant.html', form=form, plants_to_water=int(cp['water']['plants_to_water']))


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
    return render_template('temp.html', plants_to_water=int(cp['water']['plants_to_water']))


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
    return render_template('sql_db_select.html', form=form, plants_to_water=int(cp['water']['plants_to_water']))


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
    return render_template('sql_query.html', form=form, tables=tables, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/sql_result/<database>/<query>')
def sql_result(database, query):
    print(database)
    print(query)
    (columns, rows) = read_sql(database, query)
    print(columns)
    print(rows)
    return render_template('sql_result.html', columns=columns, rows=rows, database=database, query=query, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/data_plant_overview/')
def data_plant_overview():
    plant_overview_charts(cp['g']['plant_db_path'] + 'my_plants.db', getcwd() + '/static/')
    return render_template('data_plant_overview.html', plants_to_water=int(cp['water']['plants_to_water']))


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

    return render_template('data_location_select.html', form=form, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/data_location_display/<plant>')
def data_location_display(plant):
    # get plant info
    try:
        con = sql.connect(cp['g']['plant_db_path'] + 'my_plants.db')
        cur = con.cursor()
        cur.execute('select ID from houseplants where name="' + plant + '"')
        id = cur[0]
        con.close()
        print('found plant')
        (c, p) = read_row(cp['g']['plant_db_path'] + 'my_plants.db', 'houseplants', 'ID', id)
        is_plant = 1
        is_other = 0
    except Exception as e:
        p = plant
        print(e)
        is_plant = 0
        is_other = 1

    # get sensor data
    try:
        data = get_all_plant_data(cp['g']['name'], plant)
    except Exception as e:
        print(e)
    print(data)

    return render_template('data_location_display.html', p=p, data=data, is_plant=is_plant, is_other=is_other, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/data_charting_select/', methods=['GET', 'POST'])
def data_charting_select():
    return render_template('temp.html', plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/data_forecast/', methods=['GET', 'POST'])
def data_forecast():
    return render_template('temp.html', plants_to_water=int(cp['water']['plants_to_water']))

'''
@app.route('/settings/', methods=['GET', 'POST'])
def settings():
    form = Settings()
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

    return render_template('settings.html', form=form, current=current)
'''

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
        return redirect(url_for('settings'))

    return render_template('settings_add_loc.html', form=form, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/settings/', methods=['GET', 'POST'])
def settings():
    form = Settings()
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
    form.latitude.data = cp.get('g', 'latitude')
    form.longitude.data = cp.get('g', 'longitude')

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

    return render_template('settings.html', form=form, current=current, plants_to_water=int(cp['water']['plants_to_water']))


# Set of pages to read system logs
@app.route('/log_select/', methods=['GET', 'POST'])
def log_select():
    form = logSelect()
    form.log.choices = files_in_dir(dname + '/logs/')
    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        print(result)
        return redirect(url_for('log_result', file=result[0]))
    return render_template('log_select.html', form=form, plants_to_water=int(cp['water']['plants_to_water']))


@app.route('/log_result/<file>', methods=['GET', 'POST'])
def log_result(file):
    result = read_log(dname + '/logs/' + file)
    return render_template('log_result.html', file=file, result=result, plants_to_water=int(cp['water']['plants_to_water']))


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
    cp.read('config.ini')  # needed to make water badge update each time a page is loaded
    return response



if __name__ == '__main__':
    # '0.0.0.0' = 127.0.0.1 i.e. localhost
    # port = 5000 : we can modify it for localhost
    app.run(host='0.0.0.0', port=5000, debug=True)  # local webserver : app.run()
