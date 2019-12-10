from flask_wtf import Form
from wtforms import TextField, PasswordField, SelectField, BooleanField
from wtforms.fields.html5 import EmailField, DateField
from wtforms.validators import DataRequired, EqualTo, Length, Email
from datetime import date

class RegisterForm(Form):
    email = EmailField(
        'School Email', validators=[DataRequired(), Email()]
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

# Create Meal Form
class CreateMealForm(Form):
    mealDate = DateField(
        'Date of Meal (YYYY-MM-DD)', default=date.today, validators=[DataRequired()]
    )
    description = TextField(
        'Description of Meal (max: 150 characters)', validators=[DataRequired(), Length(max=150)]
    )
    dinnerBool = BooleanField(
        'Is the meal a dinner?'
    )



