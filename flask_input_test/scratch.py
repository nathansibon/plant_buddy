from configparser import ConfigParser
from os import path, chdir

def init_config(config):

    config['g'] = {
        'name': 'pi_1',
        'pi_serial': '1000000003de0361',
        'timezone': 'US/Pacific',
        'temp_scale': 'C',
        'location': 'elephant-ear',
        'ideal_vpd': 1,
        'weather_api_key': 'b11f2da9834b6beebc7319ba8c8429e7',
        'latitude': 37.775350,
        'longitude': -122.454470,
        'temp_humid': 'dht22',
        'temp_humid_pin': 4,
        'light': 'veml7700',
        'light_pin': '3 & 5',
        'soil_moisture': 'none',
        'soil_moisture_pin': 'none'
    }

    with open('test_config.ini', 'w') as f:
        config.write(f)

abspath = path.abspath(__file__)
dname = path.dirname(abspath)
chdir(dname)

cp = ConfigParser()

if not path.isfile('test_config.ini'):
    init_config(cp)

cp.read('test_config.ini')
for i in cp.sections():
    print(cp.options(i))



#cp.set('g','name','changed!')
print(cp['g']['name'])

#with open('test_config.ini', 'w') as f:
#    cp.write(f)
