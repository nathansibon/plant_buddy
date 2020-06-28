import pandas as pd
from sqlite3 import *
from function_library import *
from config import *
import logging, os, datetime

def do():

    # Initialize global SQL functions
    conn = connect(name + '_data.db')
    cur = conn.cursor()
    yesterday = pd.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - pd.Timedelta('1 days')

    sql = 'SELECT * FROM indoor_raw WHERE date_time > datetime("' + str(yesterday) + '")'
    indoor_yesterday = pd.read_sql_query(sql, conn)
    indoor_yesterday['date_time'] = pd.to_datetime(indoor_yesterday.date_time)
    print(indoor_yesterday)
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
        update_web_vars_daily(data)
    except Exception as e:
        logging.info('Update Daily Web Vars Failed')
        logging.info(e)

    return


# Set all paths to the current directory so cron job will not crash, but code will still run if you move files later...
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

logging.basicConfig(filename='logs/process_daily.log',level=logging.INFO)
logging.info('script started @ ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# general purpose error handling to log file. very helpful when executing from cron since you don't see errors
try:
    do()
except Exception as e:
    logging.exception('Error in main')
    print(e)#logging.info(e)

logging.info('completed @ ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')