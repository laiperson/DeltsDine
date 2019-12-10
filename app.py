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
isAdmin = False

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

@app.route('/meals', defaults={'date': datetime.datetime.now(timezone).date()}, strict_slashes=False)
@app.route('/meals/<date>', strict_slashes=False)
def meals(date):
    # If no date is provided, use default date of right now
    if date is None:
        date = datetime.datetime.now(timezone).date()
    else:
        if type(date) == str:
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        date = datetime.datetime(date.year, date.month, date.day).date()
    
    mealTuples = []     # each entry is (LunchMeal, DinnerMeal)
    days_of_cur_week = get_days_in_cur_week(date)

    for day in days_of_cur_week:
        try:
            # Get meal for lunch on this day
            lunchMeal = session.query(Meal).filter(Meal.Date == day, Meal.DinnerBool == False).first()

            # Get meal for dinner on this day
            dinnerMeal = session.query(Meal).filter(Meal.Date == day, Meal.DinnerBool == True).first()

            mealTuples.append((lunchMeal, dinnerMeal))
        except Exception as e:
            print("meals() threw an error when trying to get week meals. {}".format(e))
            render_template('errors/500.html'), 500

    return render_template('pages/meals.html', Meals=mealTuples, WeekDates=days_of_cur_week, Date=date)



#----------------------------------------------------------------------------#
# Helper Functions
#----------------------------------------------------------------------------#
def can_check_in(meal, checkedInBoolean):
    print("can_check_in calls has_swipes() for {} which returns {}".format(current_user, has_swipes()))
    hasSwipes = has_swipes()

    if (meal.Date == datetime.datetime.now(timezone).date()) and hasSwipes:
        # Initialize CheckIn range times to dinner hours
        checkInStartTime = datetime.time(16, 30, 0)
        checkInEndTime = datetime.time(19, 30, 0)

        dinnerBool = session.query(Meal).filter(Meal.MealId == meal.MealId).first().DinnerBool

        # Check if meal is dinner so time window for check-in can be adjusted to lunch hours
        if not dinnerBool:
            checkInStartTime = datetime.time(11, 30, 0)
            checkInEndTime = datetime.time(13, 30, 0) 

        return (checkInStartTime <= datetime.datetime.now(timezone).time() <= checkInEndTime) and not checkedInBoolean
    else:
        if not hasSwipes:
            flash("Unfortunately, you do not have any swipes left this week :(")
        return False

def get_days_in_cur_week(from_date=datetime.datetime.now(timezone).date()):
    daysList = []
    date = from_date
    day_index = date.isoweekday()
    
    # Get the date of Sunday
    sunday = date - datetime.timedelta(days=day_index)
    monday = sunday + datetime.timedelta(days=1)

    for i in range(0, 5):
        day = monday + datetime.timedelta(days=i)
        daysList.append(day)

    return daysList


# TODO! Implement query to count number of meals in CheckIn table from the past week
def has_swipes():
    swipesPerWeekAllowance = current_user.MealAllowance
    weekdays = get_days_in_cur_week()
    swipesUsedThisWeek = 0

    for i in range(0, 5):
        date = weekdays[i]

        # Get meals on this date
        meals = session.query(Meal).filter(Meal.Date == date) 
        if meals is not None:
            for meal in meals:
                userCheckIn = session.query(CheckIn).filter(CheckIn.MealId == meal.MealId, CheckIn.Email == current_user.Email).first()

                if userCheckIn is not None:
                    swipesUsedThisWeek += 1
    
    print("has_swipes found {} swipes used this week with allowance of {}. Returns {}".format(swipesUsedThisWeek, swipesPerWeekAllowance, (swipesUsedThisWeek + 1) <= swipesPerWeekAllowance))

    return ((swipesUsedThisWeek + 1) <= swipesPerWeekAllowance)



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
        print("get_meal function returned error on meal id of {}. {}".format(mealId, str(e)))
        return render_template('errors/404.html'), 404


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

            if session.query(Meal).filter(Meal.Date == date, Meal.DinnerBool == dinnerBool).first() is None:
                session.add(meal)
                session.commit()

                print("Meal added. {}".format(meal))
                flash("Success! The Meal was added.")
                return redirect(url_for('meals'))
            else:
                flash("Already added a meal for this date and time. Please try another day or time.")
                return render_template('forms/addMeal.html', form=form)
        except Exception as e:
            session.rollback()
            print("add_meal function returned error on adding meal with descr of {}. {}".format(description, str(e)))
            return render_template('errors/500.html'), 500
    else:
        print(form.errors)
        return render_template('forms/addMeal.html', form=form)

# Get last week meal schedule
@app.route('/meals/last_week')
def get_last_week_meals():
    cur_date_string = request.args.get('current_date')
    cur_date = datetime.datetime.strptime(cur_date_string, "%Y-%m-%d")
    weekBefore = cur_date - datetime.timedelta(days=7)

    return redirect(url_for('meals', date=weekBefore.date()))

# Get last week meal schedule
@app.route('/meals/next_week')
def get_next_week_meals():
    cur_date_string = request.args.get('current_date')
    cur_date = datetime.datetime.strptime(cur_date_string, "%Y-%m-%d")
    weekBefore = cur_date + datetime.timedelta(days=7)

    return redirect(url_for('meals', date=weekBefore.date()))

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
        if can_check_in(meal, canCheckInBool) and has_swipes():
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
                    Active = True,
                    IsAdmin = False
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




