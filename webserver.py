from flask import Flask, render_template
from config import *
import csv

app = Flask(__name__)

@app.route('/')
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

    # Get the daily of the variables from CSV
    reader = csv.reader(open('webpage_daily_data.csv'))
    for row in reader:
        if row[0] == '':
            pass
        else:
            data[row[0]] = row[1]

    return render_template('index.html', **data)

# this method sets the chart images to expire after 5 mins so the browser will fetch new images instead of using the cache
@app.after_request
def add_header(response):
    response.cache_control.max_age = 300
    response.cache_control.public = True
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')