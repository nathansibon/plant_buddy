from flask import Flask, render_template, request, redirect, url_for
from forms import *
from os import path, chdir
from lib import *

abspath = path.abspath(__file__)
dname = path.dirname(abspath)
chdir(dname)

app = Flask(__name__) # application 'app' is object of class 'Flask'
app.config['SECRET_KEY'] = 'sparklingcider' #TODO change to random number
init_database('my_plants')


#-----------------------------------------------------------------------------------------------------------#


@app.route('/', methods=['GET', 'POST'])  # root : main page
def index():
    return render_template('index.html')


@app.route('/test/')
def test():
    item = {'f1': 'first', 'f2': 'second'}
    form = TestForm(f1='first')
    #form.populate_obj(item)
    return render_template('test.html', form=form)


@app.route('/my_plants/')
def my_plants():
    (columns, rows) = read_plant()
    return render_template('my_plants.html', columns=columns, rows=rows)


@app.route('/add_plant/', methods=['GET', 'POST'])
def add_plant():
    form = NewPlant()
    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        for i in add_last_plant_vars():
            result.append(i)
        add_plant_to_database('my_plants', result)
        return redirect(url_for('my_plants'))
    return render_template('add_plant.html', form=form)


@app.route('/edit_plant/<id>', methods=['GET', 'POST'])
def edit_plant(id):
    print('id='+str(id))
    (columns, row) = read_row('my_plants', 'houseplants', 'ID', id)
    sub_row = {}
    for i in range(1,6):
        sub_row.update({columns[i] : row[i]})
    form = EditPlant()
    #form.process(sub_row)
    if form.is_submitted():
        result = get_form_data(list(request.form.values()))
        print('form result:')
        print(result)

        #check if the pot size changed, if so update the "last re-pot" date
        if result[4] != row[5]:
            result.append(date.today().strftime('%Y/%m/%d'))
        else:
            result.append(row[12])

        update_plant(id, result)
        return redirect(url_for('my_plants'))
    return render_template('edit_plant.html', form=form, id=id, row=row)


@app.route('/list_req/')
def list_requirements():
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

#-----------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':
    # '0.0.0.0' = 127.0.0.1 i.e. localhost
    # port = 5000 : we can modify it for localhost
    app.run(port=5000, debug=True) # local webserver : app.run()