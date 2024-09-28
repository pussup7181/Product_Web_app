from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, FloatField, FileField
)
from wtforms.validators import (
    DataRequired, Length, EqualTo, ValidationError
)
from flask_wtf.file import FileAllowed, FileRequired
from models import User

class LoginForm(FlaskForm):
    username = StringField(
        'Username', validators=[DataRequired(), Length(min=2, max=150)]
    )
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField(
        'Username', validators=[DataRequired(), Length(min=2, max=150)]
    )
    password = PasswordField(
        'Password', validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'That username is taken. Please choose a different one.'
            )

class AddItemForm(FlaskForm):
    article_number = StringField('Article Number', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    size_in_mm = FloatField('Size (mm)', validators=[DataRequired()])
    weight_in_g = FloatField('Weight (g)', validators=[DataRequired()])
    photo = FileField('Photo', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files are allowed!')
    ])
    submit_button = SubmitField('Add Item')

class SearchForm(FlaskForm):
    search_term = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

class DeleteForm(FlaskForm):
    submit = SubmitField('Delete')

class LogoutForm(FlaskForm):
    submit = SubmitField('Logout')
