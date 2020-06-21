from flask import Flask, render_template
from webpage_sensor_data import *
from webpage_daily_data import *
from config import *

app = Flask(__name__)

@app.route('/')
def index():

    f_name = name.replace('_', '')
    f_location = location.replace('_', '')

    data = {
        'time' : read_time,
        'name' : f_name,
        'location' : f_location,
        'indoor_drybulb' : indoor_drybulb,
        'indoor_rh' : indoor_rh,
        'outdoor_drybulb' : outdoor_drybulb,
        'outdoor_rh' : outdoor_rh,
        'yesterday_drybulb_max' : yesterday_drybulb_max,
        'yesterday_drybulb_min' : yesterday_drybulb_min,
        'yesterday_rh_max' : yesterday_rh_max,
        'yesterday_rh_min' : yesterday_rh_min
    }

    return render_template('index.html', **data)

@app.after_request
def add_header(response):
    response.cache_control.max_age = 300
    response.cache_control.public = True
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
