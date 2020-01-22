#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request, jsonify, flash, url_for, redirect, abort
from flask_login import current_user, login_user, logout_user, login_required, LoginManager
from flask_bcrypt import Bcrypt
from django.utils.http import url_has_allowed_host_and_scheme
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from forms import RegisterForm, LoginForm, ForgotForm, ResetPasswordForm, CreateMealForm, AddAdminForm
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
import os
import datetime
import pytz
import pickle
import os.path
import base64


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
timezone = pytz.timezone('US/Central')

if str(os.environ['APP_SETTINGS']) == "config.DevelopmentConfig":
    isDevelopment = True
else:
    isDevelopment = False

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
@app.teardown_appcontext
def shutdown_session(exception=None):
    session.close()

# Gmail API Configuration
creds = None
SCOPES = ['https://mail.google.com/']
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('gmail', 'v1', credentials=creds)


#----------------------------------------------------------------------------#
# Page Controllers.
#----------------------------------------------------------------------------#
@app.route('/')
def home():
    return render_template('pages/home.html')

@app.route('/googlea5d2b5587fcf08de.html')
def verification():
    return render_template('pages/googlea5d2b5587fcf08de.html')


@app.route('/about')
def about():
    return render_template('pages/about.html')

@app.route('/meals', defaults={'date': datetime.datetime.now(timezone).date()}, strict_slashes=False)
@app.route('/meals/<date>', strict_slashes=False)
@login_required
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

@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add_admin():
    if not current_user.is_authenticated and not current_user.IsAdmin:
        return redirect(url_for('home'))

    form = AddAdminForm(request.form)
    allMembers = session.query(Member).all()
    form.member.choices = [(member.Email, "{} {}".format(member.FirstName, member.LastName)) for member in allMembers]

    if form.validate_on_submit():
        # Check if member is already admin, don't do anything
        chosenMember = session.query(Member).filter(Member.Email == form.member.data, Member.IsAdmin == True).first()
        if chosenMember is None:
            member = session.query(Member).filter(Member.Email == form.member.data).first()
            member.IsAdmin = True

            session.commit()
            flash("Successfully added {} {} as an administator of Delts Dine.".format(member.FirstName, member.LastName))
            return redirect(url_for('home'))
        else:
            flash("{} {} is already an administrator.".format(chosenMember.FirstName, chosenMember.LastName))
            return render_template('forms/addAdmin.html', form=form)
    else:
        return render_template('forms/addAdmin.html', form=form)


#----------------------------------------------------------------------------#
# Helper Functions
#----------------------------------------------------------------------------#
def can_check_in(meal, checkedInBoolean):
    print("can_check_in calls has_swipes() for {} which returns {}".format(current_user, has_swipes()))
    hasSwipes = has_swipes()

    if (meal.Date == datetime.datetime.now(timezone).date()) and hasSwipes:
        # Initialize CheckIn range times to dinner hours
        checkInStartTime = datetime.time(16, 30, 0)
        checkInEndTime = datetime.time(18, 15, 0)

        dinnerBool = session.query(Meal).filter(Meal.MealId == meal.MealId).first().DinnerBool

        # Check if meal is dinner so time window for check-in can be adjusted to lunch hours
        if not dinnerBool:
            checkInStartTime = datetime.time(10, 45, 0)
            checkInEndTime = datetime.time(13, 15, 0)

        return (checkInStartTime <= datetime.datetime.now(timezone).time() <= checkInEndTime) and not checkedInBoolean
    else:
        if not hasSwipes:
            flash("Unfortunately, you do not have any swipes left this week :(")
        return False

def can_rsvp(meal):
    rsvpDeadline = meal.Date - datetime.timedelta(days=1)
    rsvpTimeHolder = datetime.datetime(rsvpDeadline.year, rsvpDeadline.month, rsvpDeadline.day, 17, 0, 0, 0, timezone)
    currentTime = datetime.datetime.now(timezone)

    print("can_rsvp: current time is {} while deadline is: {}. Returns {}".format(currentTime, rsvpTimeHolder, currentTime <= rsvpTimeHolder))

    if (currentTime <= rsvpTimeHolder):
        return True
    
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

def create_message(to_address, subject, message_text):
    """Create a message for an email.

    Args:
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.

    Returns:
        An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text, 'html')
    message['to'] = to_address
    message['from'] = "deltsdine@gmail.com"
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

def send_message(service, message):
    """Send an email message.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        message: Message to be sent.

    Returns:
        Sent Message.
    """
    try:
        message = (service.users().messages().send(userId="deltsdine@gmail.com", body=message)
                .execute())
        return message
    except Exception as error:
        print("An error occurred with Gmail API send_message: {}".format(error))

# Send Confirmation Email
def sendConfirmationEmail(email):
    member = session.query(Member).filter(Member.Email == email).first()
    if member is not None:
        if isDevelopment:
            link = "http://127.0.0.1:5000/ConfirmEmail/{}".format(email)
        else:
            link = "https://deltsdine.herokuapp.com/ConfirmEmail/{}".format(email)
        
        html = "<html><h3>Hi {},</h3><p>Thank you for registering for DeltsDine! Please use <a href='{}'>this link</a> to finish your registration.</p><p>All the best,</p><p>DeltsDine</p></html>".format(member.FirstName, link)
        message = create_message(
            email, 
            "Confirming Your Email for DeltsDine", 
            html
        )
    else:
        html = "<html><h3>Hi,</h3><p>Thank you for registering for DeltsDine! Please use <a href='{}'>this link</a> to finish your registration.</p><p>All the best,</p><p>DeltsDine</p></html>".format(link)
        message = create_message(
            email, 
            "Confirming Your Email for DeltsDine", 
            html
        )
    send_message(service, message)

# Send forgot your password email
# Send Confirmation Email
def sendForgotPasswordEmail(email):
    if isDevelopment:
        link = "http://127.0.0.1:5000/ResetPassword/{}".format(email)
    else:
        link = "https://deltsdine.herokuapp.com/ResetPassword/{}".format(email)

    html = "<html><h3>Hello,</h3><p>To reset your password for DeltsDine, please use <a href='{}'>this link</a> to reset your password.</p><p>Thanks,</p><p>DeltsDine</p></html>".format(link)
    message = create_message(
        email, 
        "Reset Password for DeltsDine", 
        html
    )
    send_message(service, message)


# Query to count number of meals in CheckIn table from the past week and see if they have swipes left in their allowance
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
@login_required
def get_meal(mealId):
    try:
        # fetch meal from id
        meal = session.query(Meal).filter(Meal.MealId == mealId).first()

        isRsvpd = False

        # see if current user is checked in to this meal already, as well as whether or not they are able to checkin
        checkedInBool = session.query(CheckIn).filter(CheckIn.MealId == meal.MealId, CheckIn.Email == current_user.Email).first() is not None
        canCheckIn = can_check_in(meal, checkedInBool)

        # see if it is a valid time to RSVP   **** Logic: cannot RSVP for a meal anytime after 5 PM CST the day BEFORE meal ****
        canRSVP = can_rsvp(meal)

        # initialize rsvps and check-ins lists
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
        
        return render_template('pages/view_meal.html', meal=meal, RSVPs=rsvps, CheckIns=checkIns, IsRsvpd=isRsvpd, CanCheckIn=canCheckIn, CheckedIn=checkedInBool, CanRSVP=canRSVP)
    except Exception as e:
        print("get_meal function returned error on meal id of {}. {}".format(mealId, str(e)))
        return render_template('errors/404.html'), 404


# Create a Meal
@app.route('/meals/add', methods = ['GET','POST'])
@login_required
def add_meal():
    if not current_user.IsAdmin:
        flash("Cannot access this page unless you hold administrative privileges.")
        return redirect(url_for("home"))
    
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
@login_required
def get_last_week_meals():
    cur_date_string = request.args.get('current_date')
    cur_date = datetime.datetime.strptime(cur_date_string, "%Y-%m-%d")
    weekBefore = cur_date - datetime.timedelta(days=7)

    return redirect(url_for('meals', date=weekBefore.date()))

# Get last week meal schedule
@app.route('/meals/next_week')
@login_required
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
@login_required
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
@login_required
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
@login_required
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
                    IsAdmin = False,
                    ConfirmedEmail = False
                )
                member._set_password(form.password.data)
                session.add(member)
                session.commit()
                sendConfirmationEmail(member.Email)
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


@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    form = ForgotForm(request.form)

    if form.validate_on_submit():
        member = session.query(Member).filter(Member.Email == form.email.data).first()
        if member is not None:
            sendForgotPasswordEmail(form.email.data)
            flash("We just sent you an email to reset your password. Please follow the email link to finish this process.")

            return redirect(url_for('home'))
        else:
            flash("Could not find the member. Please contact an administrator.")
            return redirect(url_for('home'))
    else:
        print(form.errors)
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
# Gmail API Controller.
#----------------------------------------------------------------------------#
@app.route('/ConfirmEmail/<email>')
def confirmEmail(email):
    member = session.query(Member).filter(Member.Email == email).first()

    if member is not None:
        member.ConfirmedEmail = True
        session.commit()
        print("Successfully confirmed email for {}".format(email))
        flash("Successfully confirmed your email!")
        return(redirect(url_for('home')))
    else:
        print("Could not confirm email for {}".format(email))
        flash("Could not confirm your email. Please contact the admin.")
        return(redirect(url_for('home')))

@app.route('/ResetPassword/<email>', methods=['GET', 'POST'])
def resetPassword(email):
    form = ResetPasswordForm(request.form)

    if form.validate_on_submit():
        member = session.query(Member).filter(Member.Email == email).first()
        if member is not None:
            member._set_password(form.password.data)
            session.commit()
            flash("Succcesfully reset your password! Please login using the new password.")
            print("Successfully changed password for {} to {}".format(email, form.password.data))

            return redirect(url_for('login'))
        else:
            flash("Could not find the member. Please contact an administrator.")
            return redirect(url_for('home'))
    else:
        print(form.errors)
        return render_template('forms/resetPassword.html', form=form)

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()




