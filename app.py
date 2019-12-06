#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request, jsonify, flash, url_for, redirect, abort
from flask_login import current_user, login_user, logout_user, LoginManager
from flask_bcrypt import Bcrypt
from django.utils.http import url_has_allowed_host_and_scheme
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from forms import RegisterForm, LoginForm, ForgotForm, CreateMealForm
import os

from models import Meal, Member, RSVP, CheckIn

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Bcrypt for Hashing Password
bcrypt = Bcrypt(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Configure DB Connection with SQLAlchemy
Base = declarative_base()

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)

session = Session()

# Get DB SQLAlchemy for Migration
db = SQLAlchemy(app)

# Automatically tear down SQLAlchemy.
'''
@app.teardown_request
def shutdown_session(exception=None):
    session.remove()
'''
@app.teardown_appcontext
def shutdown_session(exception=None):
    session.close()

# Login required decorator.
'''
def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap
'''

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#
@app.route('/')
def home():
    return render_template('pages/home.html')


@app.route('/about')
def about():
    return render_template('pages/about.html')

@app.route('/meals')
def meals():
    return render_template('pages/meals.html')

# ===== Meals Routes ===== #

# Get Meal using MealId
@app.route('/meals/view/<mealId>', methods = ['GET'])
def get_meal(mealId):
    try:
        meal = session.query(Meal).filter(Meal.MealId == mealId).first()
        return jsonify(meal.serialize())
    except Exception as e:
        return("get_meal function returned error on meal id of {}. {}".format(mealId, str(e)))

# Create a Meal
@app.route('/meals/add', methods = ['GET', 'POST'])
def add_meal():
    form = CreateMealForm(request.form)

    if form.validate_on_submit():
        date = form.mealDate.data
        description = form.description.data
        dinnerBool = form.dinnerBool.data

        try:
            meal = Meal(
                Date=date,
                Description=description,
                DinnerBool=dinnerBool
            )

            session.add(meal)
            session.commit()

            print("Meal added. {}".format(meal))
            flash("Success! The Meal was added.", 'error')
            return redirect(url_for('meals'))
        except Exception as e:
            session.rollback()
            print("add_meal function returned error on adding meal with descr of {}. {}".format(description, str(e)))
            return render_template('errors/500.html'), 500
    else:
        print(form.errors)
        return render_template('forms/addMeal.html', form=form)

# Get All Members RSVP'd to a Meal
@app.route('/meals/<MealId>/RSVPs')
def get_meal_rsvps(MealId):
    try:
        membersEmail = session.query(RSVP).filter(RSVP.MealId == MealId).all()
        return "in get meal rsvps. Got objects: {}".format(membersEmail)
    except Exception as e:
        print("Error in get_meals_rsvps route. {}".format(e))
        flash("Could not get RSVPs :( We will work on figuring this issue out.")
        return None



# ===== Authentication/User Identity Routes ===== #
@app.route('/login', methods=['GET', 'POST'])
def login():
    "current_user.is_authenticated is {}".format(current_user.is_authenticated)
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm(request.form)

    if form.validate_on_submit():
        member = session.query(Member).filter(Member.Email == form.email.data).first()
        print(member)
        if member is None or not member.is_correct_password(form.password.data):
            flash("Invalid username or password. Please try again.")
            return redirect(url_for('login'))
        
        login_user(member)
        next = request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        '''
        if not url_has_allowed_host_and_scheme(next, ['127.0.0.1:5000/login']):
            return abort(400)
        '''

        return redirect(next or url_for('home'))

    else:
        print(form.errors)
        return render_template('forms/login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    # Check if member with email already exists. If not, create user and add to DB
    if session.query(Member).filter(Email = form.email.data).first() is None:
        form = RegisterForm(request.form)
        if form.validate_on_submit():
            member = Member(
                Email = form.email.data, 
                FirstName = form.firstName.data, 
                LastName = form.lastName.data,
                MealAllowance = form.mealAllowance.data,
                WeekMealsUsed = 0,
                Active = True
                # EmailConfirmed = False
            )
            member._set_password(form.password.data)
            session.add(member)
            session.commit()
            flash('Congratulations! You have successfully registered for Delts Dine. Make sure to confirm your email, and please login.')
            return redirect(url_for('login'))
        else:
            print(form.errors)
            return render_template('forms/register.html', form=form)
    else:
        flash("A member with this email already exits")
        return render_template('forms/register.html', form=form)


@app.route('/forgot')
def forgot():
    form = ForgotForm(request.form)
    return render_template('forms/forgot.html', form=form)

@login_manager.user_loader
def get_member(Email):
    try:
        current_member = session.query(Member).get(str(Email))
        print("successfully got current member. {}".format(current_member))
        return current_member
    except Exception as e:
        print("Could not get member. {}".format(e))
        return None


# Error handlers.
@app.errorhandler(500)
def internal_error(error):
    session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()




