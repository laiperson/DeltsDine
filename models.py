from app import db, engine, bcrypt
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Boolean, Date, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref
from flask_login import UserMixin



Base = declarative_base()

class Meal(Base, UserMixin, db.Model):
    __tablename__ = 'Meal'

    MealId = db.Column(Integer, primary_key=True)
    Date = db.Column(Date)
    Description = db.Column(String())
    DinnerBool = db.Column(Boolean)

    def __init(self, MealId, Date, Description, DinnerBool):
        self.MealId = MealId
        self.Date = Date
        self.Description = Description
        self.DinnerBool = DinnerBool

    def __repr__(self):
        return "<Meal(MealId={}, Date={}, Description={}, DinnerBool={})>\n".format(self.MealId, self.Date, self.Description, self.DinnerBool)

    def serialize(self):
        return {
            'MealId': self.MealId,
            'Date': self.Date,
            'Description': self.Description,
            'DinnerBool': self.DinnerBool
        }

class Member(Base, UserMixin, db.Model):
    __tablename__ = 'Member'

    Email = Column(String(), primary_key=True)
    _Password = Column(String(128))
    FirstName = Column(String())
    LastName = Column(String())
    MealAllowance = Column(Integer)
    WeekMealsUsed = Column(Integer)
    Active = Column(Boolean)
    ConfirmedEmail = Column(Boolean)
    IsAdmin = Column(Boolean)

    def __init(self, Email, _Password, FirstName, LastName, MealAllowance, WeekMealsUsed, Active, ConfirmedEmail, IsAdmin):
        self.Email = Email
        self.FirstName = FirstName
        self.LastName = LastName
        self.MealAllowance = MealAllowance
        self.WeekMealsUsed = WeekMealsUsed
        self.Active = Active
        self.ConfirmedEmail = True          # Change this once email system is established
        self._Password = None
        self.IsAdmin = False

    @hybrid_property
    def password(self):
        return self._Password

    def get_id(self):
        return (self.Email)

    def _set_password(self, plainTextPassword):
        self._Password = bcrypt.generate_password_hash(plainTextPassword).decode('utf8')

    def is_correct_password(self, plainTextPassword):
        return bcrypt.check_password_hash(self._Password, plainTextPassword)

    def __repr__(self):
        return "<Member(Email={}, FirstName={}, LastName={}, MealAllowance={}, WeekMealsUsed={}, Active={}, ConfirmedEmail={}, IsAdmin={})>\n".format(self.Email, self.FirstName, self.LastName, self.MealAllowance, self.WeekMealsUsed, self.Active, self.ConfirmedEmail, self.IsAdmin)

    def serialize(self):
        return {
            'Email': self.Email,
            'FirstName': self.FirstName,
            'LastName': self.LastName,
            'MealAllowance': self.MealAllowance,
            'WeekMealsUsed': self.WeekMealsUsed,
            'Active': self.Active, 
            'ConfirmedEmail': self.ConfirmedEmail,
            'IsAdmin': self.IsAdmin
        }

class RSVP(Base, UserMixin, db.Model):
    __tablename__ = 'RSVP'

    MealId = Column(Integer, ForeignKey(Meal.MealId, ondelete="CASCADE"), primary_key=True)
    Email = Column(String(), ForeignKey(Member.Email, ondelete="CASCADE"), primary_key=True)
    Timestamp = Column(DateTime(timezone=True))

    Meal = relationship('Meal', backref=backref('Meal_RSVP_association'))
    Member = relationship('Member', backref=backref('Member_RSVP_association'))

    def __init(self, MealId, Email, Timestamp):
        self.MealId = MealId
        self.Email = Email
        self.Timestamp = Timestamp

    def __repr__(self):
        return "<RSVP(MealId={}, Email={}, Timestamp={})>\n".format(self.MealId, self.Email, self.Timestamp)

    def serialize(self):
        return {
            'MealId': self.MealId,
            'Email': self.Email,
            'Timestamp': self.Timestamp
        }


class CheckIn(Base, UserMixin, db.Model):
    __tablename__ = 'CheckIn'

    MealId = Column(Integer, ForeignKey(Meal.MealId), primary_key=True)
    Email = Column(String(), ForeignKey(Member.Email), primary_key=True)
    Timestamp = Column(DateTime(timezone=True))

    Meal = relationship('Meal', backref=backref('Meal_CheckIn_association'))
    Member = relationship('Member', backref=backref('Member_CheckIn_association'))

    def __init(self, MealId, Email, Timestamp):
        self.MealId = MealId
        self.Email = Email
        self.Timestamp = Timestamp

    def __repr__(self):
        return "<CheckIn(MealId={}, Email={}, Timestamp={})".format(self.MealId, self.Email, self.Timestamp)

    def serialize(self):
        return {
            'MealId': self.MealId,
            'Email': self.Email,
            'Timestamp': self.Timestamp
        }

Base.metadata.create_all(engine)