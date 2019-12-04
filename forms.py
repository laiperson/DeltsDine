from flask_wtf import Form
from wtforms import TextField, PasswordField, SelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, EqualTo, Length, Email

class RegisterForm(Form):
    email = EmailField(
        'School Email', validators=[DataRequired(), Email(), Length(min=16, max=16, message="Email must be a valid UMN email (length == 16)")]
    )
    firstName = TextField(
        'First Name', validators=[DataRequired(), Length(max=35)]
    )
    lastName = TextField(
        'Last Name', validators=[DataRequired(), Length(max=35)]
    )
    mealAllowance = SelectField("Number of Meals a Week", choices=[(3, '3'), (10, '10')], validators=[DataRequired()], coerce=int)
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message="Passwords must match")])
    confirm = PasswordField('Re-enter your password', validators=[DataRequired()])


class LoginForm(Form):
    email = EmailField(
        'School Email', validators=[DataRequired(), Email(), Length(min=16, max=16)]
    )
    password = PasswordField(
        'Password', validators=[DataRequired()]
    )


class ForgotForm(Form):
    email = TextField(
        'Email', validators=[DataRequired(), Length(min=16, max=16)]
    )


