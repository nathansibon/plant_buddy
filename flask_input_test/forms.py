from flask_wtf import FlaskForm
import wtforms as wt
from wtforms.fields import html5 as wt5
from datetime import datetime
from lib import *

class TestForm(FlaskForm):

    f1 = wt.StringField('Field 1')
    f2 = wt.StringField('Field 2')


class NewPlant(FlaskForm):

    name = wt.StringField('Name')
    species = wt.SelectField('Species', choices=combined_name)
    location = wt.StringField('Location')
    purchase_date = wt5.DateField('Purchase Date', format='%Y-%m-%d', default=datetime.today)
    pot_size = wt5.DecimalField('Pot Size (in)')
    leaf_temp_offset = wt5.DecimalField('Leaf Temperature Offset (deg C)')
    #pic = wt.FileField('Picture')
    submit = wt.SubmitField('Add')


class EditPlant(FlaskForm):

    name = wt.StringField('Name')
    species = wt.SelectField('Species', choices=combined_name)
    location = wt.StringField('Location')
    purchase_date = wt5.DateField('Purchase Date', format='%Y-%m-%d', default=datetime.today)
    pot_size = wt5.DecimalField('Pot Size (in)')
    leaf_temp_offset = wt5.DecimalField('Leaf Temperature Offset (deg C)')
    #pic = wt.FileField('Picture')
    submit = wt.SubmitField('Update')


class NewReqPlant(FlaskForm):

    species = wt.StringField('Botanical Name')
    common_name = wt.StringField('Common Name')

    light_high = wt.SelectField('Light - High', choices=key.light.dropna().tolist())
    light_low =  wt.SelectField('Light - Low', choices=key.light.dropna().tolist())

    temp_high = wt.SelectField('Temperature - High', choices=key.temp.dropna().tolist())
    temp_low = wt.SelectField('Temperature - Low', choices=key.temp.dropna().tolist())

    rh_high = wt.SelectField('Humidity - High', choices=key.rh.dropna().tolist())
    rh_low = wt.SelectField('Humidity - Low', choices=key.rh.dropna().tolist())

    water_high = wt.SelectField('Water - High', choices=key.water.dropna().tolist())
    water_low = wt.SelectField('Water - Low', choices=key.water.dropna().tolist())

    soil_cat = wt.SelectField('Soil Type', choices=key.soil.dropna().tolist())

    submit = wt.SubmitField('Add')


class GenSearch(FlaskForm):

    search = wt5.SearchField('search')
    submit = wt.SubmitField('Submit')