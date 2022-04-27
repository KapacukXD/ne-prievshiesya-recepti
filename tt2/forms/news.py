from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    ingr = TextAreaField("Ингридиенты")
    content = TextAreaField("Способ приготовления")
    is_private = BooleanField("Личное")
    submit = SubmitField('Применить')