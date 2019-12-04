from app import db
from sqlalchemy import Table, Column, Integer, ForeignKey


class Meal(db.Model):
    __tablename__ = 'Meal'

    MealId = db.Column(db.Integer, primary_key=True)
    Date = db.Column(db.Date)
    Description = db.Column(db.String())
    DinnerBool = db.Column(db.Boolean)

    def __init(self, MealId, Date, Description, DinnerBool):
        self.MealId = MealId
        self.Date = Date
        self.Description = Description
        self.DinnerBool = DinnerBool

    def __repr__(self):
        return '<Meal(MealId='%i', Date='%s', Description='%s', DinnerBool='%s')>\n'.format(self.MealId, self.Date, self.Description, self.DinnerBool)

    def serialize(self):
        return {
            'MealId': self.MealId,
            'Date': self.Date,
            'Description': self.Description,
            'DinnerBool': self.DinnerBool
        }


class Member(db.Model):
    __tablename__ = 'Member'

    Email = db.Column(db.String(length=16), primary_key=True)
    FirstName = db.Column(db.String())
    LastName = db.Column(db.String())
    MealAllowance = db.Column(db.Integer)
    WeekMealsUsed = db.Column(db.Integer)
    Active = db.Column(db.Boolean)

    def __init(self, Email, FirstName, LastName, MealAllowance, WeekMealsUsed, Active):
        self.Email = Email
        self.FirstName = FirstName
        self.LastName = LastName
        self.MealAllowance = MealAllowance
        self.WeekMealsUsed = WeekMealsUsed
        self.Active = Active

    def __repr__(self):
        return '<Member(Email='%s', FirstName='%s', LastName='%s', MealAllowance='%i', WeekMealsUsed='%i', Active='%s')>\n'.format(self.Email, self.FirstName, self.LastName, self.MealAllowance, self.WeekMealsUsed, self.Active)

    def serialize(self):
        return {
            'Email': self.Email,
            'FirstName': self.FirstName,
            'LastName': self.LastName,
            'MealAllowance': self.MealAllowance,
            'WeekMealsUsed': self.WeekMealsUsed,
            'Active': self.Active
        }


class RSVP(db.Model):
    __tablename__ = 'RSVP'

    MealId = db.Column(db.Integer, ForeignKey(Meal.MealId), primary_key=True)
    Email = db.Column(db.String(length=16), ForeignKey(Member.Email), primary_key=True)
    Timestamp = db.Column(db.DateTime(timezone=True))

    def __init(self, MealId, Email, Timestamp):
        self.MealId = MealId
        self.Email = Email
        self.Timestamp = Timestamp

    def __repr__(self):
        return '<RSVP(MealId='%i', Email='%s', Timestamp='%s')>\n'.format(self.MealId, self.Email, self.Timestamp)

    def serialize(self):
        return {
            'MealId': self.MealId,
            'Email': self.Email,
            'Timestamp': self.Timestamp
        }


class CheckIn(db.Model):
    __tablename__ = 'CheckIn'

    MealId = db.Column(db.Integer, ForeignKey(Meal.MealId), primary_key=True)
    Email = db.Column(db.String(length=16), ForeignKey(Member.Email), primary_key=True)
    Timestamp = db.Column(db.DateTime(timezone=True))

    def __init(self, MealId, Email, Timestamp):
        self.MealId = MealId
        self.Email = Email
        self.Timestamp = Timestamp

    def __repr__(self):
        return '<CheckIn(MealId='%i', Email='%s', Timestamp='%s')'.format(self.MealId, self.Email, self.Timestamp)

    def serialize(self):
        return {
            'MealId': self.MealId,
            'Email': self.Email,
            'Timestamp': self.Timestamp
        }
