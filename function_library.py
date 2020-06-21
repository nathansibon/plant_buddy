import math, numpy, sqlite3, time, logging, pyowm
import pandas as pd
import numpy as np
from config import *
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# These packages will raise an error if not running this code on a Pi
# Adding this error handling will allow coding and debugging on PC
try:
    import board, adafruit_dht
except:
    print('not connected to pi, problematic libraries not imported')
    pass

# All the magical functions in gen. order: gathering raw data, calculate metrics, non-weather stuff, database functions

def get_outdoor_weather():

    owm = pyowm.OWM(weather_api_key)
    obs_list = owm.weather_at_coords(latitude, longitude)
    weather = obs_list.get_weather()

    drybulb = weather.get_temperature(unit='celsius')['temp']  # drybulb in C
    rh = weather.get_humidity() / 100  # % relative humidity
    clouds = weather.get_clouds() / 100  # % cloud cover
    if weather.get_rain() == {}:
        rain = 0
    else:
        rain = weather.get_rain()  # mm of precipitation
        rain = rain.get('1h')
    wind = weather.get_wind()['speed']  # meters/second
    status = weather.get_status()  # string description of current weather

    sunrise = pd.to_datetime(weather.get_sunrise_time('iso'))
    sunrise = sunrise.tz_convert(tz=timezone)

    sunset = pd.to_datetime(weather.get_sunset_time('iso'))
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

def get_indoor_weather():

    # Initial the dht device, with data pin connected to:
    dhtDevice = adafruit_dht.DHT22(board.D4)

    output = [
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        pi_serial,
        location
    ]

    # Unfortunately, this sensor doesn't always read correctly so error handling and noise reduction is included
    max = 5
    drybulb = []
    humid = []

    while len(drybulb) < max:

        try:
            temp_drybulb = dhtDevice.temperature
            temp_humid = round(dhtDevice.humidity / 100, 2)  # convert RH from "50%" to "0.50" to match outdoor weather format and work in calculations
        except:
            logging.info('Error reading Temp-Humid Sensor, retrying...')
            continue

        drybulb.append(temp_drybulb)
        humid.append(temp_humid)

        # The DHT22 is reportedly slow at reading, this wait hopefully prevents a bad read (i.e. wildly different than it should be) on fail
        time.sleep(2)

    output.append(std_filter(drybulb, 1, 2))
    output.append(std_filter(humid, 1, 2))

    # output is [0] datetime [1] serial [2] location [3] drybulb [4] rh
    return output

def calc_outdoor_weather(data):

    temp = [
        wet_bulb(data[1],data[2]),
        dew_point(data[1],data[2]),
    ]

    # new list is now [0] DATE_TIME, [1] TEMPERATURE, [2] RELATIVE HUMIDITY, [3] CLOUD COVER, [4] PRECIPITATION, [5] WET BULB, [6] DEW POINT
    data.append(temp[0])
    data.append(temp[1])

    return data

def calc_indoor_weather(data):

    temp = [
        wet_bulb(data[3], data[4]),
        dew_point(data[3], data[4]),
    ]

    # new list is now [0] datetime [1] serial [2] location [3] drybulb [4] rh [5] wet bulb [6] dew point
    data.append(temp[0])
    data.append(temp[1])

    return data

def wet_bulb(temp_C, rh):
    # Calculate the wet-bulb temperature using the Stull formula (valid between 5%-99% RH and -20 to 50 degrees C. source: https://www.omnicalculator.com/physics/wet-bulb#how-to-calculate-the-wet-bulb-temperature

    rh = rh * 100

    output = temp_C * numpy.arctan(0.151977 *
                                   (rh + 8.313659) ** (1 / 2)) + \
             numpy.arctan(temp_C + rh) - \
             numpy.arctan(rh - 1.676331) + 0.00391838 * \
             rh ** (3 / 2) * numpy.arctan(0.023101 * rh) - 4.686035
    # Returns Wet bulb in C

    output = round(output, 2)

    return output

def dew_point(temp_C, rh):
    #Dew point is a measure of moisture capacity of the air at certain temp and pressure. This is a better indicator of comfort than RH
    #Calculate the dew point using the Magnus-Tetens formula (Sonntag90) that allows us to obtain accurate results (with an uncertainty of 0.35°C) for temperatures ranging from -45°C to 60°C. source: https://www.omnicalculator.com/physics/dew-point#howto

    a = 17.62
    b = 243.12

    alpha = math.log(rh,2.71828) + a * temp_C / (b + temp_C)

    output = (b * alpha) / (a - alpha)

    output = round(output, 2)

    return output

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
        "dewpoint real)"
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
        dewpoint
        )
        VALUES(?,?,?,?,?,?,?)
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
        "dewpoint real)"
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
        dewpoint
        ) 
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
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

    return

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
                                column_name + '_rate'])

    # Note: only works if index is Datetime

    # Create empty dataframe for adding caclulated stats
    day_data = pd.DataFrame(columns=column_list)

    logging.info('current day = ' + datetime.now().strftime("%d"))

    # Loop through each day and calculate stats for each
    for day in set(outdoor.index.day):

        logging.info('processing day '+str(day))

        if len(outdoor[outdoor.index.day == day].index) > 85:  # Check if data is full 24 hours (or close enough, 90th percentile)
            logging.info('full day')
        #if day != datetime.now().strftime("%d"): # Only process if data collection for the day is over
            d_data = outdoor[outdoor.index.day == day]  # Make working dataframe of only today's data

            date = d_data.index[:1].date[0]
            values = {}

            for (column_name, column_data) in d_data.iteritems():

                if d_data[column_name].dtype == 'float64':
                    # Find min, max and range of data
                    d_max = d_data[column_name].max()
                    d_min = d_data[column_name].min()
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

                    max_time = max_time.time()
                    min_time = min_time.time()

                    values.update(
                        {column_name + '_max': d_max, column_name + '_max_time': max_time, column_name + '_min': d_min,
                         column_name + '_min_time': min_time, column_name + '_range': d_range, column_name + '_period':
                             period, column_name + '_rate': rate})

            if d_data[(d_data.index.hour > 7) & (d_data.index.hour < 20)].clouds.mean() > 0.3:
                sun = 1
            else:
                sun = 0

            values.update({'sun': sun})
            row = pd.Series(values, name=date)
            day_data = day_data.append(row)

        else:
            logging.info('Partial Day, # of entries = ' + str(len(outdoor[outdoor.index.day == day].index)))
            #logging.info('Found todays data, pass')

    return day_data

def process_daily_indoor(conn, sql):

    # New pandas dataframe with datetime as index
    indoor = pd.read_sql_query(sql, conn)
    indoor['date_time'] = pd.to_datetime(indoor.date_time)
    indoor.set_index('date_time', inplace=True)

    # Get list of columns from dataframe to be processed and set up column names of new dataframe
    column_list = []
    for (column_name, column_data) in indoor.iteritems():
        if indoor[column_name].dtype == 'float64':
            column_list.extend([column_name + '_max', column_name + '_max_time', column_name + '_min',
                                column_name + '_min_time', column_name + '_range', column_name + '_period',
                                column_name + '_rate'])

    # Note: only works if index is Datetime

    # Create empty dataframe for adding caclulated stats
    day_data = pd.DataFrame(columns=column_list)

    logging.info('current day = ' + datetime.now().strftime("%d"))

    # Loop through each day and calculate stats for each
    for day in set(indoor.index.day):

        logging.info('processing day '+str(day))
        if len(indoor[indoor.index.day == day].index) > 85:  # Check if data is full 24 hours (or close enough, 90th percentile)
            logging.info('full day')
        #if str(day) != datetime.now().strftime("%d"): # Only process if data collection for the day is over

            d_data = indoor[indoor.index.day == day]  # Make working dataframe of only today's data

            date = d_data.index[:1].date[0]
            values = {}

            for (column_name, column_data) in d_data.iteritems():

                if d_data[column_name].dtype == 'float64':
                    # Find min, max and range of data
                    d_max = d_data[column_name].max()
                    d_min = d_data[column_name].min()
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

                    max_time = max_time.time()
                    min_time = min_time.time()

                    values.update(
                        {column_name + '_max': d_max, column_name + '_max_time': max_time, column_name + '_min': d_min,
                         column_name + '_min_time': min_time, column_name + '_range': d_range,
                         column_name + '_period': period, column_name + '_rate': rate})

                    values.update({column_name: column_data[0]})

            # values = {'Drybulb Max': d_max, 'Max Time': max_time, 'Drybulb Min': d_min, 'Min Time': min_time, 'Drybulb Range': d_range, 'Warm Up Time': warm_up_time}
            row = pd.Series(values, name=date)
            day_data = day_data.append(row)

        else:
            logging.info('Partial Day, # of entries = ' + str(len(indoor[indoor.index.day == day].index)))
            #logging.info('Found todays data, pass')

    # update yesterday section for webpage with last row of processed data
    update_web_vars_daily(row)

    return day_data

def update_web_vars_sensor(indoor, outdoor):

    file = open(r'webpage_sensor_data.py','r+')

    text = [
        "read_time = '"+time.strftime("%H:%M:%S", time.localtime())+"'\n",
        "indoor_drybulb = '"+str(math.floor(indoor[3]))+"'\n",
        "indoor_rh = '"+str(math.floor(indoor[4]*100))+"'\n",
        "\n",
        "outdoor_drybulb = '" + str(math.floor(outdoor[1])) + "'\n",
        "outdoor_rh = '" + str(math.floor(outdoor[2]*100)) + "'\n",
    ]

    file.writelines(text)
    file.close()

    return

def update_web_vars_daily(data):

    file = open(r'webpage_daily_data.py','r+')

    file.truncate(0)
    file.seek(0)

    text = [
        "yesterday_drybulb_max = '" + str(math.floor(data.drybulb_max)) + "'\n",
        "yesterday_drybulb_min = '" + str(math.floor(data.drybulb_min)) + "'\n",
        "yesterday_rh_max = '" + str(math.floor(data.rh_max * 100)) + "'\n",
        "yesterday_rh_min = '" + str(math.floor(data.rh_min * 100)) + "'"
    ]

    file.writelines(text)
    file.close()

    return

def update_web_charts(db_path):

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    last_week = pd.Timestamp.now() - pd.Timedelta('7 days')
    last_week = last_week.round('min')

    # get previous week worth of data for chart
    sql = 'SELECT date_time, drybulb, rh FROM indoor_raw WHERE date_time > datetime("' + str(last_week) + '")'
    indoor = pd.read_sql_query(sql, conn)
    indoor['date_time'] = pd.to_datetime(indoor.date_time)
    indoor.set_index('date_time', inplace=True)

    # get previous week worth of data for chart
    sql = 'SELECT date_time, drybulb, rh FROM outdoor_raw WHERE date_time > datetime("' + str(last_week) + '")'
    outdoor = pd.read_sql_query(sql, conn)
    outdoor['date_time'] = pd.to_datetime(outdoor.date_time)
    outdoor.set_index('date_time', inplace=True)

    # create drybulb plot
    fig, ax = plt.subplots(figsize=(15, 5))
    plt.title('Drybulb')
    ax.plot(indoor.drybulb, label='Indoor', alpha=.8)
    ax.plot(outdoor.drybulb, label='Outdoor', alpha=.8)
    plt.ylim(5, 35)
    ax.legend()
    #ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.grid(b=True, which='major', color='grey')
    ax.yaxis.grid(b=True, which='major', color='grey')
    fig.autofmt_xdate()
    ax.fmt_xdata = mdates.DateFormatter('%m-%d')
    plt.savefig('static/last_week_drybulb.png')
    plt.close()

    # create rh plot
    fig, ax = plt.subplots(figsize=(15, 5))
    plt.title('Relative Humidity')
    ax.plot(indoor.rh, label='Indoor', alpha=.8)
    ax.plot(outdoor.rh, label='Outdoor', alpha=.8)
    plt.ylim(0, 1)
    ax.legend()
    #ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.grid(b=True, which='major', color='grey')
    ax.yaxis.grid(b=True, which='major', color='grey')
    fig.autofmt_xdate()
    ax.fmt_xdata = mdates.DateFormatter('%m-%d')
    plt.savefig('static/last_week_rh.png')
    plt.close()

    conn.close()

    return


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