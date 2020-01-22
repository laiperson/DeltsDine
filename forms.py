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
        'School Email', validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'Password', validators=[DataRequired()]
    )


class ForgotForm(Form):
    email = TextField(
        'Email', validators=[DataRequired()]
    )

class ResetPasswordForm(Form):
    password = PasswordField('New password', validators=[DataRequired(), EqualTo('confirm', message="Passwords must match")])
    confirm = PasswordField('Re-enter your new password', validators=[DataRequired()])

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

# Add an Admin Form
class AddAdminForm(Form):
    member = SelectField(label="Member", validators=[DataRequired()])

# Edit a Member's Profile Information Form
class EditMemberForm(Form):
    member = SelectField(label="Member", validators=[DataRequired()])
    mealAllowance = SelectField("Number of Meals a Week", choices=[(3, '3'), (4, '4'), (5, '5'),  (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')], validators=[DataRequired()], coerce=int)



