from flask_wtf import FlaskForm
import wtforms as wt
from wtforms.fields import html5 as wt5
from datetime import datetime
from lib_webserver import *


class NewPlant(FlaskForm):

    name = wt.StringField('Unique Name')
    species = wt.SelectField('Species')
    location = wt.StringField('Location')
    purchased_from = wt.StringField('Purchased From')
    purchase_date = wt5.DateField('Purchase Date', format='%Y-%m-%d', default=datetime.today)
    watering_schedule = wt.IntegerField('Watering Schedule (days)', default=7)
    last_watered = wt5.DateField('Last Watered', format='%Y-%m-%d', default=datetime.today)
    substrate = wt.SelectField('Substrate')
    pot_size = wt5.DecimalField('Pot Size (in)', default=4)
    leaf_temp_offset = wt5.DecimalField('Leaf Temperature Offset (deg C)', default=0)
    ignore = wt.BooleanField('Ignore')
    #pic = wt.FileField('Picture') THIS IS CURRENTLY DONE IN THE HTML FILE
    submit = wt.SubmitField('Add')


class EditPlant(FlaskForm):
    # note: "last repot date" field will auto-update if the pot size changes, see flask server code
    location = wt.StringField('Location')
    watering_schedule = wt.IntegerField('Watering Schedule (days)')
    last_watered = wt5.DateField('Last Watered', format='%Y-%m-%d')
    substrate = wt.SelectField('Substrate')
    pot_size = wt5.DecimalField('Pot Size (in)')
    leaf_temp_offset = wt5.DecimalField('Leaf Temperature Offset (deg C)')
    ignore = wt.BooleanField('Ignore during watering')
    #pic = wt.FileField('Picture') THIS IS CURRENTLY DONE IN THE HTML FILE
    submit = wt.SubmitField('Update')


class NewJournal(FlaskForm):

    title = wt.StringField(render_kw={'placeholder': 'Title'})
    plant = wt.SelectField()
    body = wt.TextAreaField(render_kw={'placeholder': 'Journal body...'})
    #pic = wt.FileField('Picture') THIS IS CURRENTLY DONE IN THE HTML FILE
    submit = wt.SubmitField()


class FilterJournal(FlaskForm):

    plant = wt.SelectField()
    submit = wt.SubmitField()


class ReqPlant(FlaskForm):

    species = wt.StringField('Botanical Name')
    common_name = wt.StringField('Common Name')

    light_high = wt.SelectField('Light - High')
    light_low = wt.SelectField('Light - Low')

    temp_high = wt.SelectField('Temperature - High')
    temp_low = wt.SelectField('Temperature - Low')

    rh_high = wt.SelectField('Humidity - High')
    rh_low = wt.SelectField('Humidity - Low')

    water_high = wt.SelectField('Water - High')
    water_low = wt.SelectField('Water - Low')

    soil_cat = wt.SelectField('Soil Type')

    submit = wt.SubmitField('Submit')


class sqlDBselect(FlaskForm):

    database = wt.SelectField('Database')
    submit = wt.SubmitField('Submit')


class sqlQuery(FlaskForm):

    sql = wt.StringField('query', render_kw={'placeholder': 'Enter Database Query'})
    submit = wt.SubmitField('Submit')


class GenSelect(FlaskForm):

    choice = wt.SelectField()
    submit = wt.SubmitField()


class SettingsBasic(FlaskForm):

    name = wt.StringField('Name')
    timezone = wt.SelectField('Time Zone')
    temp_scale = wt.SelectField('Temperature Scale', choices=['C', 'F'])
    location = wt.SelectField('Current Location')
    ideal_vpd = wt5.DecimalField('Ideal VPD')
    submit = wt.SubmitField('Update')


class NewLocation(FlaskForm):

    name = wt.StringField('Name')
    submit = wt.SubmitField('Add')


class SettingsAdvanced(FlaskForm):

    name = wt.StringField('Name')
    timezone = wt.SelectField('Time Zone')
    temp_scale = wt.SelectField('Temperature Scale', choices=['C', 'F'])
    location = wt.SelectField('Current Location')
    ideal_vpd = wt5.DecimalField('Ideal VPD')
    weather_api_key = wt.StringField('OpenWeatherMap API Key')
    latitude = wt5.DecimalField('Latitude')
    longitude = wt5.DecimalField('Longitude')
    temp_humid = wt.BooleanField('Temperature/Humidity Sensor')
    light = wt.BooleanField('Light Sensor')
    soil_moisture = wt.BooleanField('Soil Moisture Sensor')
    submit = wt.SubmitField('Update')


class logSelect(FlaskForm):

    log = wt.SelectField('file')
    submit = wt.SubmitField('submit')


class Test(FlaskForm):

    check = wt.BooleanField('check', false_values='0')
    submit = wt.SubmitField('Add')
