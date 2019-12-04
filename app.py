#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from forms import RegisterForm, LoginForm, ForgotForm
import os

from models import Meal, Member, RSVP, CheckIn

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Base = declarative_base()

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)

session = Session()

# Automatically tear down SQLAlchemy.
'''
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()
'''

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

# ===== Meals Routes ===== #
@app.route('/meals')
def meals():
    return render_template('pages/meals.html')

@app.route('/meals/<id>')
def get_meal(id):
    try:
        meal = session.query(Meal).filter(Meal.MealId == id).first()
        return jsonify(meal.serialize())
    except Exception as e:
        return("get_meal function returned error on meal id of {}. {}".format(id, str(e)))

@app.route('/meals/add')
def add_meal():
    date = request.args.get('date')
    description = request.args.get('description')
    dinnerBool = request.args.get('dinnerBool')

    try:
        meal = Meal(
            Date=date,
            Description=description,
            DinnerBool=dinnerBool
        )

        session.add(meal)
        session.commit()

        return "Meal added with MealId={}".format(meal.MealId)
    except Exception as e:
        session.rollback()
        return "add_meal function returned error on adding meal with descr of {}. {}".format(description, str(e))

@app.route('/meals/<id>/RSVPs')
def get_meal_rsvps(id):
    membersEmail = session.query(RSVP).filter(RSVP.MealId == id)
    print("in get meal rsvps")
    return membersEmail



# ===== Authentication/User Identity Routes ===== #
@app.route('/login')
def login():
    form = LoginForm(request.form)
    return render_template('forms/login.html', form=form)


@app.route('/register')
def register():
    form = RegisterForm(request.form)
    return render_template('forms/register.html', form=form)


@app.route('/forgot')
def forgot():
    form = ForgotForm(request.form)
    return render_template('forms/forgot.html', form=form)


# Error handlers.
@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
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




