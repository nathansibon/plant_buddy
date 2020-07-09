# General Info
name = 'pi_1'   # This should correspond to the name of your pi and will define the name of the database
pi_serial = 'XXXXXXXXXXXXXXXX'
timezone = 'US/Pacific'     # see PYTZ docs for a full list of available timezones

# Exterior info
weather_api_key = 'XXXXXXXXXXXXXXXXXXXXXXX'
latitude = 37.XXXXXX
longitude = -122.XXXXXX

# Interior info
location = 'kitchen'
sensors = {
    'temp_humid': {'name' : 'dht22',
                   'serial' : 'XXXXXXXXXXX',
                   'pin' : 4    # haven't found a way to use this in the sensor read dynamically, but this should help with remembering what goes where
                   },
    'light': 'none',
    'soil_moisture': 'none'
}

ideal_vpd = 1 # will be used to recommend a humidity level based on the drybulb temperature. Typical values are between 0.8 - 1.2 for average plants.
