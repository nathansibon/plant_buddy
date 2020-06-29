from function_library import *
import logging, time, os, datetime
from config import *

# This is where the main code is kept for this script.
# We enclose it in a function so we can wrap it in a general purpose error-handler as shown below
# This makes writing log files much simpler and will work whether it's run from the shell or a cron job
def do():

    # retrieve data from OpenWeatherMap API, then calculate additional metrics from retrieved data and append list
    outdoor = get_outdoor_weather()
    outdoor = calc_outdoor_weather(outdoor)

    # retrieve data from sensor(s), then calculate additional metrics from retrieved data and append list.
    indoor = get_indoor_all()

    # Full path of database: /home/pi/share/env_datalogger/Pi_X_data.db
    update_db(name + '_data.db', indoor, outdoor)

    update_web_vars_sensor(indoor, outdoor)
    update_web_charts(name + '_data.db')


# Set all paths to the current directory so cron job will not crash, but code will still run if you move files later...
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

logging.basicConfig(filename='logs/collect_data.log', level=logging.INFO)
logging.info('started @ ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# general purpose error handling to log file. very helpful when executing from cron since you don't see errors
try:
    do()
except Exception as e:
    logging.exception('Error in main')
    logging.info(e)

logging.info('completed @ ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')