# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, FileField
from wtforms.validators import DataRequired


class HotelForm(FlaskForm):
    name = StringField('Hotel Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    description = TextAreaField('Description')
    price_per_night = FloatField('Price per Night', validators=[DataRequired()])
    images = FileField('Hotel Image')  # Field untuk mengunggah gambar
