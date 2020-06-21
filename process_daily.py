import pandas as pd
from sqlite3 import *
from function_library import *
from config import *
import logging, os, datetime

def do():

    # Initialize global SQL functions
    conn = connect(name + '_data.db')
    cur = conn.cursor()

    logging.info('Begin Outdoor Section')

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    fetch = cur.fetchall()

    # Get only the data which hasn't been processed
    for entry in fetch:
        if entry == 'outdoor_day':
            logging.info('Previous outdoor data found')
            cur.execute('SELECT * FROM outdoor_day ORDER BY rowid DESC LIMIT 1;')
            row = cur.fetchone()
            last_row = pd.to_datetime(row[0])

            # add a time which will always be after the last daily entry (since the acutal time may vary depending on read speed)
            last_row = str(last_row.date()) + ' 23:50:00'

            # Get only the data which needs to be processed. Meh... security < convenience
            sql = 'SELECT * FROM outdoor_raw WHERE date_time > datetime("' + str(last_row) + '")'

        else:
            logging.info('New database, processing all entries')
            sql = 'SELECT * FROM outdoor_raw'

    day_data = process_daily_outdoor(conn, sql)

    # Write new data to database
    if day_data.empty == False:
        try:
            day_data.sort_index(inplace=True)
            day_data.to_sql("outdoor_day", conn, if_exists="append")
            logging.info('Data Written')
        except:
            logging.info('Write failed!')

    else:
        logging.info('day_data is empty!')

    logging.info('Begin Indoor Section')

    for entry in fetch:
        if entry == 'indoor_day':
            logging.info('Previous indoor data found')
            cur.execute('SELECT * FROM indoor_day ORDER BY rowid DESC LIMIT 1;')
            row = cur.fetchone()
            last_row = pd.to_datetime(row[0])

            # add a time which will always be after the last daily entry (since the acutal time may vary depending on read speed)
            last_row = str(last_row.date()) + ' 23:50:00'

            # Get only the data which needs to be processed. Meh... security < convenience
            sql = 'SELECT * FROM indoor_raw WHERE date_time > datetime("' + str(last_row) + '")'

        else:
            logging.info('New database, processing all entries')
            sql = 'SELECT * FROM indoor_raw'

    day_data = process_daily_indoor(conn, sql)

    # Write new data to database
    if day_data.empty == False:
        try:
            day_data.sort_index(inplace=True)
            day_data.to_sql("indoor_day", conn, if_exists="append")
            logging.info('Data Written')
        except:
            logging.info('Write failed!')

    else:
        logging.info('day_data is empty!')

    conn.close()

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

logging.info('completed @ ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')