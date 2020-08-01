# coding=utf-8

import math, numpy, sqlite3, time, logging, pyowm
import pandas as pd
import numpy as np
from config import *
import sys_var
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# These packages will raise an error if not running this code on a Pi
# Adding this error handling will allow coding and debugging on PC
try:
    import board, adafruit_dht
except Exception as e:
    print('not connected to pi, problematic libraries not imported (1 of 2)')
    print(e)
    pass

try:
    import busio, adafruit_veml7700
except Exception as e:
    print('not connected to pi, problematic libraries not imported (2 of 2)')
    print(e)
    pass

# READ SENSORS AND QUERY APIS
def get_outdoor_weather():

    owm = pyowm.OWM(weather_api_key)
    mgr = owm.weather_manager()
    obs_list = mgr.weather_at_coords(latitude, longitude)
    weather = obs_list.weather

    drybulb = weather.temperature(unit='celsius')['temp']  # drybulb in C
    rh = weather.humidity / 100  # % relative humidity
    clouds = weather.clouds / 100  # % cloud cover
    if weather.rain == {}:
        rain = 0
    else:
        rain = weather.rain  # mm of precipitation
        rain = rain.get('1h')
    wind = weather.wind()['speed']  # meters/second
    status = weather.status  # string description of current weather

    sunrise = pd.to_datetime(weather.sunrise_time('iso'))
    sunrise = sunrise.tz_convert(tz=timezone)

    sunset = pd.to_datetime(weather.sunset_time('iso'))
    sunset = sunset.tz_convert(tz=timezone)

    output = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        drybulb,
        rh,
        clouds,
        rain,
        wind,
        status,
        str(sunrise),
        str(sunset)
    ]

    return output

def get_indoor_all():

    output = [
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        pi_serial,
        location
    ]

    if sensors.get('temp_humid') != 'none':
        # output is [0] datetime [1] serial [2] location [3] drybulb [4] rh
        for i in get_indoor_weather():
            output.append(i)

        # output is now [0] datetime [1] serial [2] location [3] drybulb [4] rh [5] wet bulb [6] dew point, [7] vapor pressure deficit [8] rh for vpd [9] white_light [10] lux
        output = calc_indoor_weather(output)
    else:
        print('No temp/humidity sensor listed, adding placeholders')
        for i in range(6):
            output.append(0)

    if sensors.get('light') != 'none':
        # output is [0] datetime [1] serial [2] location [3] drybulb [4] rh [5] wet bulb [6] dew point, [7] vapor pressure deficit [8] rh for vpd [9] white_light [10] lux
        for i in get_indoor_light():
            output.append(i)
    else:
        print('No light sensor listed, adding placeholders')
        for i in range(2):
            output.append(0)

    # TODO add soil moisture sensor

    return output

def get_indoor_weather():

    # Initial the dht device, with data pin connected to:
    dhtDevice = adafruit_dht.DHT22(board.D4)

    # Unfortunately, this sensor doesn't always read correctly so error handling and noise reduction is included
    max = 5
    drybulb = []
    humid = []
    output = []

    while len(drybulb) < max:

        # The DHT22 is reportedly slow at reading, this wait hopefully prevents a bad read (i.e. wildly different than it should be) on fail
        time.sleep(2)

        try:
            temp_drybulb = dhtDevice.temperature
            temp_humid = round(dhtDevice.humidity / 100, 2)  # convert RH from "50%" to "0.50" to match outdoor weather format and work in calculations
        except:
            print('Error reading Temp-Humid Sensor, retrying...')

        drybulb.append(temp_drybulb)
        humid.append(temp_humid)
    output.append(std_filter(drybulb, 1, 2))
    output.append(std_filter(humid, 1, 2))

    return output

def get_indoor_light():

    i2c = busio.I2C(board.SCL, board.SDA)
    light = adafruit_veml7700.VEML7700(i2c)

    max = 5
    white = []  # white light channel includes a ~flat response from ~550 nm to ~850 nm, consistent with important wavelengths for plant energy. not super clear from doc but appears to be in SI lux
    lux = []  # band-pass filter reading centered at ~550 nm, apparently correlates well to human perception of brightness. in SI lux.
    output = []

    while len(white) < max:

        try:
            temp_white = light.white
            temp_lux = light.lux
        except:
            print('Error reading Light Sensor, retrying...')
            continue

        white.append(temp_white)
        lux.append(temp_lux)

        time.sleep(1)

    output.append(std_filter(white, 1, 1))
    output.append(std_filter(lux, 1, 1))

    return output

# COMPILED CALCS
def calc_outdoor_weather(data):

    temp = [
        wet_bulb(data[1], data[2]),
        dew_point(data[1], data[2]),
        vpd(data[1], data[2])
    ]

    # new list is now [0] DATE_TIME, [1] TEMPERATURE, [2] RELATIVE HUMIDITY, [3] CLOUD COVER, [4] RAIN, [5] WIND, [6] STATUS, [7] SUNRISE, [8] SUNSET, [9] WET BULB, [10] DEW POINT, [11] Vapor Pressure Deficit
    data.append(temp[0])
    data.append(temp[1])
    data.append(temp[2])

    return data

def calc_indoor_weather(data):

    temp = [
        wet_bulb(data[3], data[4]),
        dew_point(data[3], data[4]),
        vpd(data[3], data[4]),
        rh_for_vpd(data[3], ideal_vpd)
    ]

    # new list is now [0] datetime [1] serial [2] location [3] drybulb [4] rh [5] wet bulb [6] dew point, [7] vapor pressure deficit, [8] rh for vpd
    for i in temp:
        data.append(i)

    return data

# INDIVIDUAL METRIC CALCULATIONS
def wet_bulb(temp_c, rh):
    # Calculate the wet-bulb temperature using the Stull formula (valid between 5%-99% RH and -20 to 50 degrees C. source: https://www.omnicalculator.com/physics/wet-bulb#how-to-calculate-the-wet-bulb-temperature

    rh = rh * 100

    output = temp_c * numpy.arctan(0.151977 *
                                   (rh + 8.313659) ** (1 / 2)) + \
             numpy.arctan(temp_c + rh) - \
             numpy.arctan(rh - 1.676331) + 0.00391838 * \
             rh ** (3 / 2) * numpy.arctan(0.023101 * rh) - 4.686035
    # Returns Wet bulb in C

    output = round(output, 2)

    return output

def dew_point(temp_c, rh):
    #Dew point is a measure of moisture capacity of the air at certain temp and pressure. This is a better indicator of comfort than RH
    #Calculate the dew point using the Magnus-Tetens formula (Sonntag90) that allows us to obtain accurate results (with an uncertainty of 0.35°C) for temperatures ranging from -45°C to 60°C. source: https://www.omnicalculator.com/physics/dew-point#howto

    a = 17.62
    b = 243.12

    alpha = math.log(rh,2.71828) + a * temp_c / (b + temp_c)

    output = (b * alpha) / (a - alpha)

    output = round(output, 2)

    return output

def vpd(temp_c, rh):

    svp = 610.7 * math.pow(10, (7.5 * temp_c) / (237.3 + temp_c))

    vpd = np.round((svp * (1 - rh)) / 1000, 2)

    # Source used: http://cronklab.wikidot.com/calculation-of-vapour-pressure-deficit
    # Other Sources
    #   1: https://pulsegrow.com/blogs/learn/vpd#calculate
    #   2: https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit

    return vpd

def rh_for_vpd(temp_c, vpd):

    # see function vpd() for sources
    svp = 610.7 * math.pow(10, (7.5 * temp_c) / (237.3 + temp_c))
    vpd = vpd * 1000 # this equation takes Pa, not kPa.
    rh = 1 - (vpd / svp)
    rh = np.round(rh, 2)

    return rh

def getserial():
    # Extract serial from cpuinfo file. Source: https://www.raspberrypi-spy.co.uk/2012/09/getting-your-raspberry-pi-serial-number-using-python/
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial

def std_filter(data, tolerance, rounding):

    # source https://forum.dexterindustries.com/t/solved-dht-sensor-occasionally-returning-spurious-values/2939/5

    data = np.array(data)
    sd = np.std(data)

    if sd == 0:
        return np.mean(data)

    sd = sd * tolerance
    mean = np.mean(data)
    filtered = []
    for i in data:
        if mean - sd <= i <= mean + sd:
            filtered.append(i)

    output = round(np.mean(filtered), rounding)

    return output

# DATA STORAGE
def verify_db(db_path):

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = pd.read_sql_query("SELECT `name` FROM `sqlite_master` WHERE type='table'", conn)

    for tbl in sys_var.check:
        if tbl in tables.name.values:
            columns = pd.read_sql_query("PRAGMA table_info('" + tbl + "')", conn)
            for col in sys_var.check.get(tbl):
                if col[0] in columns.name.values:
                    pass
                elif col[0] == 'index':
                    pass
                else:
                    print('Table ' + tbl + 'missing column' + col[0] + ', adding to db')
                    cur.execute('ALTER TABLE ' + str(tbl) + ' ADD COLUMN ' + str(col[0]) + ' ' + col[1])
                    conn.commit()
 
        else:
            print('missing table: ' + tbl)
            sql = 'create table if not exists ' + tbl + ' ('
            for i, txt in enumerate(sys_var.check.get(tbl)):
                if i == len(sys_var.check.get(tbl)) - 1:
                    sql = sql + txt[0] + ' ' + txt[1]
                else:
                    sql = sql + txt[0] + ' ' + txt[1] + ', '
            sql = sql + ')'
            conn.execute(sql)
            conn.commit()

    conn.close()
    print('Database ' + db_path + ' verified')


def update_db(db_path, indoor, outdoor):

    conn = sqlite3.connect(db_path)

    conn.execute(
        "create table if not exists indoor_raw"
        "(id integer primary key, "
        "date_time timestamp, "
        "pi_serial varchar(765), "
        "location varchar(765), "
        "drybulb real, "
        "rh real, "
        "wetbulb real, "
        "dewpoint real,"
        "vpd real,"
        "rh_req_for_vpd real,"
        "white_light real,"
        "lux real)"
    )

    conn.commit()

    cur = conn.cursor()

    # Create SQL command to insert data into fillable fields. primary key will auto-increment
    sql = ''' INSERT INTO indoor_raw
        (date_time,
        pi_serial,
        location,
        drybulb,
        rh,
        wetbulb,
        dewpoint,
        vpd,
        rh_req_for_vpd,
        white_light,
        lux
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
    '''

    # Execute command but substitute ? placeholders above with actual data from indoor
    cur.execute(sql, indoor)
    conn.commit()

    conn.execute(
        "create table if not exists outdoor_raw "
        "(id integer primary key, "
        "date_time timestamp, "
        "drybulb real, "
        "rh real, "
        "clouds real,"
        "rain real,"
        "wind real,"
        "status varchar(765),"
        "sunrise timestamp,"
        "sunset timestamp, "
        "wetbulb real, "
        "dewpoint real,"
        "vpd real"
        ")"
    )

    conn.commit()

    # Create SQL command to insert data into fillable fields. primary key will auto-increment
    sql = ''' INSERT INTO outdoor_raw 
        (date_time,
        drybulb, 
        rh,  
        clouds, 
        rain,
        wind,
        status,
        sunrise,
        sunset,
        wetbulb,
        dewpoint,
        vpd
        ) 
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    '''

    # Execute command but substitute ? placeholders above with actual data from indoor
    cur.execute(sql, outdoor)
    conn.commit()

    cur.close()
    conn.close()

def read_env_db(db_path):

    conn = sqlite3.connect(db_path)

    # returns a tuple of table names in this database
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER by name DESC")
    read_cur = conn.cursor()

    # two for loops are required to extract the string table name from the tuple stored in cur
    for tuple in cur:

        for table_name in tuple:

            print('Table = ' + table_name)
            # Read indoor column headers
            # unfortunately, must use this unsafe string format method since the ? placeholder does not work for table names
            read_cur.execute('PRAGMA TABLE_INFO({})'.format(table_name))
            names = [tup[1] for tup in read_cur.fetchall()]
            print('Columns = ' + str(names))

            read_cur = conn.execute("SELECT * FROM {}".format(table_name))
            for row in read_cur:
                print(row)

    cur.close()
    conn.close()


def process_daily_outdoor(conn, sql):

    # New pandas dataframe with datetime as index
    outdoor = pd.read_sql_query(sql, conn)
    outdoor['date_time'] = pd.to_datetime(outdoor.date_time)
    outdoor.set_index('date_time', inplace=True)

    # Get list of columns from dataframe to be processed and set up column names of new dataframe of daily data
    column_list = []
    for (column_name, column_data) in outdoor.iteritems():
        if outdoor[column_name].dtype == 'float64':
            column_list.extend([column_name + '_max', column_name + '_max_time', column_name + '_min',
                                column_name + '_min_time', column_name + '_range', column_name + '_period',
                                column_name + '_rate', column_name + '_mean'])

    # Note: only works if index is Datetime

    # Create empty dataframe for adding caclulated stats
    day_data = pd.DataFrame(columns=column_list)

    print('current day = ' + datetime.now().strftime("%d"))

    # Loop through each day and calculate stats for each
    for day in set(outdoor.index.day):

        print('processing day '+str(day))

        if len(outdoor[outdoor.index.day == day].index) > 85:  # Check if data is full 24 hours (or close enough, 90th percentile)
            print('full day')
        #if day != datetime.now().strftime("%d"): # Only process if data collection for the day is over
            d_data = outdoor[outdoor.index.day == day]  # Make working dataframe of only today's data

            date = d_data.index[:1].date[0]
            values = {}

            for (column_name, column_data) in d_data.iteritems():

                if d_data[column_name].dtype == 'float64' and d_data[column_name].isnull().values.any() == False:

                    # Find min, max and range of data
                    d_max = round(d_data[column_name].max(), 2)
                    d_min = d_data[column_name].min()
                    d_range = np.round(d_max - d_min, 1)
                    d_mean = d_data[column_name].mean()

                    max_time_options = d_data.index[d_data[column_name] == d_max]
                    min_time_options = d_data.index[d_data[column_name] == d_min]
                    max_time = max_time_options.mean()
                    min_time = min_time_options.mean()
                    period = max_time - min_time
                    period = round(period.seconds / 3600, 1)  # Reduce period from Timedelta to Hours

                    if period > 0.01:
                        rate = d_range / period
                    else:
                        rate = 0

                    max_time = max_time.time()
                    min_time = min_time.time()

                    values.update(
                        {column_name + '_max': d_max,
                         column_name + '_max_time': max_time,
                         column_name + '_min': d_min,
                         column_name + '_min_time': min_time,
                         column_name + '_range': d_range,
                         column_name + '_period': period,
                         column_name + '_rate': rate,
                         column_name + '_mean' : d_mean})

            if d_data[(d_data.index.hour > 7) & (d_data.index.hour < 20)].clouds.mean() > 0.3:
                sun = 1
            else:
                sun = 0

            values.update({'sun': sun})
            row = pd.Series(values, name=date)
            day_data = day_data.append(row)

        else:
            print('Partial Day, # of entries = ' + str(len(outdoor[outdoor.index.day == day].index)))

    return day_data

def process_daily_indoor(conn, sql):

    # New pandas dataframe with datetime as index
    indoor = pd.read_sql_query(sql, conn)
    indoor['date_time'] = pd.to_datetime(indoor.date_time)
    indoor.set_index('date_time', inplace=True)     # Note: only works if index is Datetime

    # Get sunrise and sunset times from the outdoor dataset so statistics for light are for daytime only
    sql = 'SELECT date_time, sunrise, sunset FROM outdoor_raw'
    outdoor = pd.read_sql_query(sql, conn)
    outdoor['date_time'] = pd.to_datetime(outdoor.date_time)
    outdoor['sunrise'] = pd.to_datetime(outdoor.sunrise)
    outdoor['sunset'] = pd.to_datetime(outdoor.sunset)

    # Get list of columns from dataframe to be processed and set up column names of new dataframe
    column_list = []
    for (column_name, column_data) in indoor.iteritems():
        if indoor[column_name].dtype == 'float64':
            column_list.extend([column_name + '_max', column_name + '_max_time', column_name + '_min',
                                column_name + '_min_time', column_name + '_range', column_name + '_period',
                                column_name + '_rate', column_name + '_mean'])

    # Create empty dataframe for adding caclulated stats
    day_data = pd.DataFrame(columns=column_list)

    print('current day = ' + datetime.now().strftime("%d"))

    # Loop through each day and calculate stats for each
    for month in set(indoor.index.month):
        for day in set(indoor[indoor.index.month == month].index.day):

            print('processing day '+str(day))
            if len(indoor[indoor.index.day == day].index) > 85:  # Check if data is full 24 hours (or close enough, 90th percentile)
                print('full day')
            #if str(day) != datetime.now().strftime("%d"): # Only process if data collection for the day is over

                d_data = indoor[indoor.index.day == day]  # Make working dataframe of only today's data
                d_sunrise = outdoor[outdoor.date_time.dt.day == day].sunrise.dt.hour.mean()
                d_sunset = outdoor[outdoor.date_time.dt.day == day].sunset.dt.hour.mean()

                date = d_data.index[:1].date[0]
                values = {}

                for (column_name, column_data) in d_data.iteritems():

                    if d_data[column_name].dtype == 'float64' and d_data[column_name].isnull().values.any() == False:

                        if column_name == 'lux' or column_name == 'white_light':

                            d_max = d_data[column_name].max()
                            max_time_options = d_data.index[d_data[column_name] == d_max].mean()
                            max_time = max_time_options.strftime('%H:%M:%S')
                            d_mean = d_data[(d_data.index.hour > d_sunrise + 1) & (
                                        d_data.index.hour < d_sunset - 1)].lux.mean()

                            values.update(
                                {column_name + '_max': d_max,
                                 column_name + '_max_time': max_time,
                                 column_name + '_mean': d_mean})

                        else:

                            # Find min, max, average and range of data
                            d_max = d_data[column_name].max()
                            d_min = d_data[column_name].min()
                            d_mean = np.round(d_data[column_name].mean(), 2)
                            d_range = np.round(d_max - d_min, 1)

                            max_time_options = d_data.index[d_data[column_name] == d_max]
                            min_time_options = d_data.index[d_data[column_name] == d_min]
                            max_time = max_time_options.mean()
                            min_time = min_time_options.mean()
                            period = max_time - min_time
                            period = round(period.seconds / 3600, 1)  # Reduce period from Timedelta to Hours

                            if period > 0.01:
                                rate = d_range / period
                            else:
                                rate = 0

                            max_time = max_time.strftime('%H:%M:%S')
                            min_time = min_time.strftime('%H:%M:%S')

                            values.update(
                                {column_name + '_max': d_max,
                                 column_name + '_max_time': max_time,
                                 column_name + '_min': d_min,
                                 column_name + '_min_time': min_time,
                                 column_name + '_range': d_range,
                                 column_name + '_period': period,
                                 column_name + '_rate': rate,
                                 column_name + '_mean': d_mean})

                row = pd.Series(values, name=date)
                day_data = day_data.append(row)

            else:
                print('Partial Day, # of entries = ' + str(len(indoor[indoor.index.day == day].index)))

    # update yesterday section for webpage with last row of processed data

    try:
        update_web_vars_daily(row)
    except Exception as e:
        print('Update Daily Web Vars Failed')
        print(e)

    return day_data

def process_yesterday(indoor_yesterday, sunrise, sunset):

    values = {}
    for (column_name, column_data) in indoor_yesterday.iteritems():
        if indoor_yesterday[column_name].dtype == 'float64' and indoor_yesterday[
            column_name].isnull().values.any() == False:

            if column_name == 'lux' or column_name == 'white_light':

                d_max = indoor_yesterday[column_name].max()
                max_time_options = indoor_yesterday.date_time[indoor_yesterday[column_name] == d_max].mean()
                max_time = max_time_options.strftime('%H:%M:%S')
                d_mean = np.round(indoor_yesterday[(indoor_yesterday.date_time.dt.hour > sunrise + 1) & (
                        indoor_yesterday.date_time.dt.hour < sunset - 1)].lux.mean(),2)

                values.update(
                    {column_name + '_max': d_max,
                     column_name + '_max_time': max_time,
                     column_name + '_mean': d_mean})

            else:

                # Find min, max, average and range of data
                d_max = indoor_yesterday[column_name].max()
                d_min = indoor_yesterday[column_name].min()
                d_mean = np.round(indoor_yesterday[column_name].mean(), 2)
                d_range = np.round(d_max - d_min, 1)
                max_time_options = indoor_yesterday.date_time[indoor_yesterday[column_name] == d_max]
                min_time_options = indoor_yesterday.date_time[indoor_yesterday[column_name] == d_min]
                max_time = max_time_options.mean()
                min_time = min_time_options.mean()
                period = max_time - min_time
                period = round(period.seconds / 3600, 1)  # Reduce period from Timedelta to Hours

                if period > 0.01:
                    rate = d_range / period
                else:
                    rate = 0
                max_time = max_time.strftime('%H:%M:%S')
                min_time = min_time.strftime('%H:%M:%S')

                values.update(
                    {column_name + '_max': d_max,
                     column_name + '_max_time': max_time,
                     column_name + '_min': d_min,
                     column_name + '_min_time': min_time,
                     column_name + '_range': d_range,
                     column_name + '_period': period,
                     column_name + '_rate': rate,
                     column_name + '_mean': d_mean})

    row = pd.Series(values)
    return row

# WEBPAGE
def update_web_vars_sensor(indoor, outdoor):

    time = pd.to_datetime(indoor[0]).strftime('%H:%M')

    if temp_scale == 'C':

        dict = {'time' : time,
                'outdoor_drybulb': str(math.floor(outdoor[1])),
                'outdoor_rh': str(math.floor(outdoor[2] * 100)),
                'outdoor_vpd': str(outdoor[11])
                }

    elif temp_scale == 'F':
        dict = {'time' : time,
                'outdoor_drybulb': str(math.floor((outdoor[1]*(9/5))+32)),
                'outdoor_rh': str(math.floor(outdoor[2] * 100)),
                'outdoor_vpd': str(outdoor[11])
                }

    if sensors.get('temp_humid') != 'none':
        if temp_scale == 'C':
            dict['indoor_drybulb'] = str(math.floor(indoor[3]))
        elif temp_scale == 'F':
            dict['indoor_drybulb'] = str(math.floor((indoor[3]*(9/5))+32))

        dict['indoor_rh'] = str(math.floor(indoor[4] * 100))
        dict['req_rh'] = str(math.floor(indoor[8] * 100))
        dict['indoor_vpd'] = str(indoor[7])
    else:
        dict['indoor_drybulb'] = 'n/a'
        dict['indoor_rh'] = 'n/a'
        dict['indoor_vpd'] = 'n/a'

    if sensors.get('light') != 'none':
        dict['indoor_lux'] = str(math.floor(indoor[10]))
    else:
        dict['indoor_lux'] = 'n/a'

    dict['temp_scale'] = temp_scale

    s = pd.Series(dict)
    s.to_csv('webpage_sensor_data.csv')

    return

def update_web_vars_daily(data):

    print('script started')
    print(data)

    metrics = [
        'drybulb',
        'rh',
        'vpd',
        'lux'
    ]

    types = [
        'mean',
        'max',
        'min',
        'max_time',
        'min_time'
    ]

    list = []

    for i in metrics:
        for j in types:
            list.append(i + '_' + j)

    dict = {}

    for i in list:
        try:
            if i in ['rh_mean', 'rh_max', 'rh_min']:
                dict['yesterday_' + i] = str(math.floor(float(data[i]) * 100))

            elif i in ['drybulb_mean', 'drybulb_max', 'drybulb_min']:
                if temp_scale == 'C':
                    dict['yesterday_' + i] = data[i]
                elif temp_scale == 'F':
                    dict['yesterday_' + i] = round(data[i] * (9.0/5.0) + 32,1)

            elif type(data[i]) is numpy.float64:
                dict['yesterday_' + i] = data[i]

            elif i[-4:] == 'time':
                dict['yesterday_' + i] = pd.to_datetime(data[i]).strftime('%H:%M')

            else:
                dict['yesterday_' + i] = data[i]

        except Exception as e:
            print('error writing dictionary')
            print(e)
            dict['yesterday_' + i] = 'n/a'

    print(dict)
    s = pd.Series(dict)
    s.to_csv('webpage_daily_data.csv')

    return

def update_web_charts(db_path):

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    last_week = pd.Timestamp.now() - pd.Timedelta('7 days')
    last_week = last_week.round('min')

    # get previous week worth of INDOOR data for chart
    if temp_scale == 'C':
        sql = 'SELECT date_time, drybulb, rh, vpd, rh_req_for_vpd, lux FROM indoor_raw WHERE location="' + location + '" AND date_time > datetime("' + str(last_week) + '")'
    elif temp_scale == 'F':
        sql = 'SELECT date_time, (drybulb * (9.0/5.0)) + 32 as drybulb, rh, vpd, rh_req_for_vpd, lux FROM indoor_raw WHERE location="' + location + '" AND date_time > datetime("' + str(last_week) + '")'
    indoor = pd.read_sql_query(sql, conn)
    indoor['date_time'] = pd.to_datetime(indoor.date_time)
    indoor.set_index('date_time', inplace=True)

    # get previous week worth of OUTDOOR data for chart
    if temp_scale == 'C':
        sql = 'SELECT date_time, drybulb, rh, vpd FROM outdoor_raw WHERE date_time > datetime("' + str(last_week) + '")'
    elif temp_scale == 'F':
        sql = 'SELECT date_time, (drybulb * (9.0/5.0)) + 32 as drybulb, rh, vpd FROM outdoor_raw WHERE date_time > datetime("' + str(last_week) + '")'
    outdoor = pd.read_sql_query(sql, conn)
    outdoor['date_time'] = pd.to_datetime(outdoor.date_time)
    outdoor.set_index('date_time', inplace=True)

    print('data retrieved, creating charts')
    print(indoor.tail())
    # create drybulb plot
    fig, ax = plt.subplots(figsize=(15, 5))
    plt.title('Drybulb')
    ax.plot(indoor.drybulb, label='Indoor', alpha=.8)
    ax.plot(outdoor.drybulb, label='Outdoor', alpha=.8)
    if temp_scale == 'C':
        plt.ylim(5, 35)
    elif temp_scale == 'F':
        plt.ylim(40,100)
    ax.legend()
    #ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.grid(b=True, which='major', color='grey')
    ax.yaxis.grid(b=True, which='major', color='grey')
    ax.tick_params(labelright=True)
    fig.autofmt_xdate()
    ax.fmt_xdata = mdates.DateFormatter('%m-%d')
    plt.savefig('static/last_week_drybulb.png')
    plt.close()

    # create rh plot
    fig, ax = plt.subplots(figsize=(15, 5))
    plt.title('Relative Humidity')
    ax.plot(indoor.rh, label='Indoor', alpha=.8)
    ax.plot(outdoor.rh.rolling(4, center=True).mean(), label='Outdoor', alpha=.8)
    ax.plot(indoor.rh_req_for_vpd, label='Indoor - Required for VPD', linestyle='dashed')
    plt.ylim(0, 1)
    ax.legend()
    #ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.grid(b=True, which='major', color='grey')
    ax.yaxis.grid(b=True, which='major', color='grey')
    ax.tick_params(labelright=True)
    fig.autofmt_xdate()
    ax.fmt_xdata = mdates.DateFormatter('%m-%d')
    plt.savefig('static/last_week_rh.png')
    plt.close()

    # create vpd plot
    fig, ax = plt.subplots(figsize=(15, 5))
    plt.title('Vapor Pressure Deficit')
    ax.plot(indoor.vpd, label='Indoor', alpha=.8)
    ax.plot(outdoor.vpd.rolling(4, center=True).mean(), label='Outdoor', alpha=.8)
    plt.ylim(0, 3)
    ax.legend()
    #ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.grid(b=True, which='major', color='grey')
    ax.yaxis.grid(b=True, which='major', color='grey')
    ax.tick_params(labelright=True)
    fig.autofmt_xdate()
    ax.fmt_xdata = mdates.DateFormatter('%m-%d')
    plt.savefig('static/last_week_vpd.png')
    plt.close()

    # create indoor lux plot
    fig, ax = plt.subplots(figsize=(15, 5))
    plt.title('Indoor Light')
    ax.plot(indoor.lux, alpha=.8)
    ax.xaxis.grid(b=True, which='major', color='grey')
    ax.yaxis.grid(b=True, which='major', color='grey')
    ax.tick_params(labelright=True)
    fig.autofmt_xdate()
    ax.fmt_xdata = mdates.DateFormatter('%m-%d')
    plt.savefig('static/last_week_lux.png')
    plt.close()

    conn.close()

    return