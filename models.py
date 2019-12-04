from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Boolean, Date, DateTime
from sqlalchemy.ext.hybrid import hybrid_property

import app

Base = declarative_base()

class Meal(Base):
    __tablename__ = 'Meal'

    MealId = Column(Integer, primary_key=True)
    Date = Column(Date)
    Description = Column(String())
    DinnerBool = Column(Boolean)

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


class Member(Base):
    __tablename__ = 'Member'

    Email = Column(String(length=16), primary_key=True)
    _Password = Column(String(128))
    FirstName = Column(String())
    LastName = Column(String())
    MealAllowance = Column(Integer)
    WeekMealsUsed = Column(Integer)
    Active = Column(Boolean)
    EmailConfirmed = Column(Boolean)

    def __init(self, Email, _Password, FirstName, LastName, MealAllowance, WeekMealsUsed, Active, EmailConfirmed):
        self.Email = Email
        self.FirstName = FirstName
        self.LastName = LastName
        self.MealAllowance = MealAllowance
        self.WeekMealsUsed = WeekMealsUsed
        self.Active = Active
        self.EmailConfirmed = True          # Change this once email system is established

    @hybrid_property
    def password(self):
        return self._Password

    @password.setter
    def _set_password(self, plainTextPassword):
        self._Password = app.bcrypt.generate_password_hash(plainTextPassword)

    def is_correct_password(self, plainTextPassword):
        return app.bcrypt.check_password_hash(self.password(), plainTextPassword)

    def __repr__(self):
        return "<Member(Email={}, FirstName={}, LastName={}, MealAllowance={}, WeekMealsUsed={}, Active={}, EmailConfirmed={})>\n".format(self.Email, self.FirstName, self.LastName, self.MealAllowance, self.WeekMealsUsed, self.Active, self.EmailConfirmed)

    def serialize(self):
        return {
            'Email': self.Email,
            'FirstName': self.FirstName,
            'LastName': self.LastName,
            'MealAllowance': self.MealAllowance,
            'WeekMealsUsed': self.WeekMealsUsed,
            'Active': self.Active, 
            'EmailConfirmed': self.EmailConfirmed
        }


class RSVP(Base):
    __tablename__ = 'RSVP'

    MealId = Column(Integer, ForeignKey(Meal.MealId), primary_key=True)
    Email = Column(String(length=16), ForeignKey(Member.Email), primary_key=True)
    Timestamp = Column(DateTime(timezone=True))

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


class CheckIn(Base):
    __tablename__ = 'CheckIn'

    MealId = Column(Integer, ForeignKey(Meal.MealId), primary_key=True)
    Email = Column(String(length=16), ForeignKey(Member.Email), primary_key=True)
    Timestamp = Column(DateTime(timezone=True))

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
