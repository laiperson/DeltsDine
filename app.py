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
import datetime
import pytz



#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
timezone = pytz.timezone('US/Central')

# Initialize Bcrypt for Hashing Password
bcrypt = Bcrypt(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Configure DB Connection with SQLAlchemy
# Base = declarative_base()

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)

session = Session()

# Get DB SQLAlchemy for Migration
db = SQLAlchemy(app)
from models import Meal, Member, RSVP, CheckIn

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
# Page Controllers.
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



#----------------------------------------------------------------------------#
# Helper Functions
#----------------------------------------------------------------------------#
def can_check_in(meal, checkedInBoolean):
    # Initialize CheckIn range times to dinner hours
    checkInStartTime = datetime.time(16, 30, 0)
    checkInEndTime = datetime.time(21, 30, 0)
    print("Check in time is between {} and {}".format(checkInStartTime, checkInEndTime))
    print("Current time is {}".format(datetime.datetime.now(timezone).time()))

    print("CheckedInBoolean is {}".format(checkedInBoolean))

    dinnerBool = session.query(Meal).filter(Meal.MealId == meal.MealId).first().DinnerBool
    print("dinner bool is {}".format(dinnerBool))

    # Check if meal is dinner so time window for check-in can be adjusted to lunch hours
    if not dinnerBool:
        checkInStartTime = datetime.time(11, 30, 0)
        checkInEndTime = datetime.time(13, 30, 0) 

    returnBool = (checkInStartTime <= datetime.datetime.now(timezone).time() <= checkInEndTime) and not checkedInBoolean
    print("can_check_in returns boolean value of {}".format(returnBool))

    return (checkInStartTime <= datetime.datetime.now(timezone).time() <= checkInEndTime) and not checkedInBoolean

# TODO! Implement query to count number of meals in CheckIn table from the past week
def has_swipes(member):
    return True



#----------------------------------------------------------------------------#
# Meal Controllers.
#----------------------------------------------------------------------------#

# Get Meal using MealId
@app.route('/meals/view/<mealId>', methods = ['GET'])
def get_meal(mealId):
    try:
        meal = session.query(Meal).filter(Meal.MealId == mealId).first()
        isRsvpd = False
        checkedInBool = session.query(CheckIn).filter(CheckIn.MealId == meal.MealId, CheckIn.Email == current_user.Email).first() is not None
        canCheckIn = can_check_in(meal, checkedInBool)
        rsvps = []
        checkIns = []
                
        # Check if user already is RSVP'd
        if session.query(RSVP).filter(RSVP.MealId == mealId, RSVP.Email == current_user.Email).first() is not None:
            isRsvpd = True
        
        # append all Member objects for members RSVPd for Meal
        for result in session.query(RSVP, Member).distinct(Member.Email).filter(RSVP.MealId == mealId, RSVP.Email == Member.Email):
            rsvps.append(result.Member)

        # append all Member objects for members CheckedIn for Meal
        for result in session.query(CheckIn, Member).distinct(Member.Email).filter(CheckIn.MealId == mealId, CheckIn.Email == Member.Email):
            checkIns.append(result.Member)
        
        return render_template('pages/view_meal.html', meal=meal, RSVPs=rsvps, CheckIns=checkIns, IsRsvpd=isRsvpd, CanCheckIn=canCheckIn, CheckedIn=checkedInBool)
    except Exception as e:
        return("get_meal function returned error on meal id of {}. {}".format(mealId, str(e)))

# Create a Meal
@app.route('/meals/add', methods = ['GET','POST'])
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
            flash("Success! The Meal was added.")
            return redirect(url_for('meals'))
        except Exception as e:
            session.rollback()
            print("add_meal function returned error on adding meal with descr of {}. {}".format(description, str(e)))
            return render_template('errors/500.html'), 500
    else:
        print(form.errors)
        return render_template('forms/addMeal.html', form=form)

# Get All Members RSVP'd to a Meal
@app.route('/meals/<int:MealId>/RSVPs')
def get_meal_rsvps(MealId):
    try:
        membersEmail = session.query(RSVP).filter(RSVP.MealId == MealId).all()
        return "in get meal rsvps. Got objects: {}".format(membersEmail)
    except Exception as e:
        print("Error in get_meals_rsvps route. {}".format(e))
        flash("Could not get RSVPs :( We will work on figuring this issue out.")
        return None

#----------------------------------------------------------------------------#
# RSVP Controllers.
#----------------------------------------------------------------------------#
# RSVP the Current Member to a Meal
@app.route('/meals/<int:MealId>/RSVP', methods=['GET', 'POST'])
def rsvp_for_meal(MealId):
    try:
        rsvp = RSVP(
            MealId = MealId,
            Email = current_user.Email,
            Timestamp = datetime.datetime.now()
        )

        # Check if user already is RSVP'd
        if session.query(RSVP).filter(RSVP.MealId == rsvp.MealId, RSVP.Email == rsvp.Email).first() is None:
            session.add(rsvp)
            session.commit()
            flash("Success! You RSVP'd.")
        else:
            flash("You were already RSVP'd for that meal.")

        return redirect(url_for("get_meal", mealId=MealId))
    except Exception as e:
        print("RSVP for Meal with ID of {} was unsuccessful. Please try again. {}".format(MealId, e))
        return redirect(url_for("get_meal", mealId=MealId))

# Delete Member's RSVP to the Current Meal
@app.route('/meals/<int:MealId>/RSVP/Delete', methods=['GET', 'DELETE'])
def delete_rsvp(MealId):
    try:
        rsvp = session.query(RSVP).filter(RSVP.MealId == MealId, RSVP.Email == current_user.Email).first()

        session.delete(rsvp)
        session.commit()
        flash("Deleted RSVP successfully!")

        return redirect(url_for("get_meal", mealId=MealId))
    except Exception as e:
        print("Deletion of RSVP for Meal with ID of {} was unsuccessful. Please try again. {}".format(MealId, e))
        return redirect(url_for("get_meal", mealId=MealId))



#----------------------------------------------------------------------------#
# CheckIn Controllers.
#----------------------------------------------------------------------------#

# CheckIn to a Meal
@app.route('/meals/<int:MealId>/CheckIn', methods=['GET', 'POST'])
def check_in(MealId):

    try:
        meal = session.query(Meal).filter(Meal.MealId == MealId).first()
        canCheckInBool = session.query(CheckIn).filter(CheckIn.MealId == MealId, CheckIn.Email == current_user.Email).first() is not None

        # Check if Member is in the time frame to check-in for a meal
        if can_check_in(meal, canCheckInBool) and has_swipes(current_user):
            checkIn = CheckIn(
                MealId = MealId,
                Email = current_user.Email,
                Timestamp = datetime.datetime.now()
            )

            # Check if user already is RSVP'd
            if session.query(CheckIn).filter(CheckIn.MealId == checkIn.MealId, CheckIn.Email == checkIn.Email).first() is None:
                session.add(checkIn)
                session.commit()

                meal = session.query(Meal).filter(Meal.MealId == MealId).first()

                flash("Check In Was a Success!")
                return render_template('pages/view_checkin.html', meal=meal)
            else:
                flash("You were already RSVP'd for that meal.")
        else:
            flash("Cannot check-in for a meal more than 30 minutes before or after.")
        return redirect(url_for("get_meal", mealId=MealId))
    except Exception as e:
        print("RSVP for Meal with ID of {} was unsuccessful. Please try again. {}".format(MealId, e))
        return redirect(url_for("get_meal", mealId=MealId))



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

    form = RegisterForm(request.form)

    if form.validate_on_submit():

        # Check if member with email already exists. If not, create user and add to DB
        if session.query(Member).filter(Member.Email == form.email.data).first() is None:
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
    else:
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




