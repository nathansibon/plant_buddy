from os import path, chdir
from datetime import datetime
from configparser import ConfigParser
from lib_datalogger import *

# This is where the main code is kept for this script.
# We enclose it in a function so we can wrap it in a general purpose error-handler as shown below
# This makes writing log files much simpler and will work whether it's run from the shell or a cron job
def do():

    # verify the user's database is properly set up and no columns are missing
    verify_db(cp['g']['name'] + '_data.db')

    # retrieve data from OpenWeatherMap API, then calculate additional metrics from retrieved data and append list
    outdoor = get_outdoor_weather()
    outdoor = calc_outdoor_weather(outdoor)

    # retrieve data from sensor(s), then calculate additional metrics from retrieved data and append list.
    indoor = get_indoor_all()

    # Full path of database: /home/pi/share/env_datalogger/Pi_X_data.db
    update_db(cp['g']['name'] + '_data.db', indoor, outdoor)

    update_web_vars_sensor(indoor, outdoor)
    update_web_charts(cp['g']['name'] + '_data.db')


# Set all paths to the current directory so cron job will not crash, but code will still run if you move files later...
abspath = path.abspath(__file__)
dname = path.dirname(abspath)
chdir(dname)
cp = ConfigParser()
cp.read('config.ini')

#logging.basicConfig(filename='logs/collect_data.log', level=print)
print('started @ ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# this 'if' is necessary to allow other scripts (such as buttons on the flask server) to trigger the system to read c_sensors, but prevent this from running on module import
if __name__ == "__main__":
    # general purpose error handling to log file. helpful when executing from cron since you don't see errors
    #try:
    do()
    #except Exception as e:
    #    print('Error in main')
    #    print(e)

    print('completed @ ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')

    exit()