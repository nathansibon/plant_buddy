from sqlite3 import *
from lib_datalogger import *
from lib_webserver import update_water
import datetime
from os import path, chdir


def do():

    # process daily sensor data
    for i in range(2):  # try three times
        # Initialize global SQL functions
        conn = connect(cp['g']['name'] + '_data.db')
        yesterday = pd.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - pd.Timedelta('1 days')

        sql = 'SELECT * FROM indoor_raw WHERE date_time > datetime("' + str(yesterday) + '")'
        indoor_yesterday = pd.read_sql_query(sql, conn)
        indoor_yesterday['date_time'] = pd.to_datetime(indoor_yesterday.date_time)
        print(indoor_yesterday.drybulb.mean())
        print('')

        sql = 'SELECT date_time, sunrise, sunset FROM outdoor_raw WHERE date_time > datetime("' + str(yesterday) + '")'
        outdoor = pd.read_sql_query(sql, conn)
        outdoor['date_time'] = pd.to_datetime(outdoor.date_time)
        outdoor['sunrise'] = pd.to_datetime(outdoor.sunrise)
        outdoor['sunset'] = pd.to_datetime(outdoor.sunset)
        sunrise = outdoor[outdoor.date_time.dt.day == yesterday.day].sunrise.min().hour
        sunset = outdoor[outdoor.date_time.dt.day == yesterday.day].sunset.min().hour

        data = process_yesterday(indoor_yesterday, sunrise, sunset)

        try:
            update_web_vars_daily(str(yesterday).split(' ')[0], data)
            break   # if update succeeded, break loop and continue
        except Exception as e:
            print('Update Daily Web Vars Failed')
            print(e)

    update_water()


# Set all paths to the current directory so cron job will not crash, but code will still run if you move files later...
abspath = path.abspath(__file__)
dname = path.dirname(abspath)
chdir(dname)
cp = ConfigParser()
cp.read('config.ini')

# logging.basicConfig(filename='logs/process_daily.log',level=print)
print('script started @ ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# general purpose error handling to log file. very helpful when executing from cron since you don't see errors
try:
    do()
except Exception as e:
    print('Error in main')
    print(e)

print('completed @ ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')
