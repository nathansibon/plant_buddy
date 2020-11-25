# this script will change every time an update modifies the data structure of the databases
# check the description of the latest commit to see if you need to run this script

from os import path, chdir
from configparser import ConfigParser
from lib_webserver import verify_db, fix_null_col

abspath = path.abspath(__file__)
dname = path.dirname(abspath)
chdir(dname)
cp = ConfigParser()
cp.read('config.ini')

verify_db(cp['g']['plant_db_path'] + 'my_plants.db')

# 2020-11-1
# RESTART THE WEBSERVER FIRST TO ADD MISSING COLUMN 'sold'
fix_null_col('my_plants.db', 'houseplants', 'sold', '0')