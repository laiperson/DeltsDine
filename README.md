***Notes for the graders:*** I will create accounts for the two TAs and the Professor that are given administrative rights. User credentials for these will be your UMN emails and 'Test' as the password. If you would like to try seeing the none administrative permissions level, please create a new account with a different, none UMN email. Please NOTE that check-ins can only happen from 4:30PM CST to 7:30PM CST for Dinners and 11:30AM CST - 1:30PM CST ON THE CORRECT DAY. The Check-In button will be disabled unless these criteria are passed. Logic for this is within the can_check_in function in the Helper Functions section of app.py

# **Delts Dine** by Ben Wiley
1. Project Type: Plan A
2. Group Members Name: none. Did alone.
3. Link to live Application: https://deltsdine.herokuapp.com/
4. Link to Github Code Repository: https://github.com/BenWileyUMN/DeltsDine
5. List of Technologies/API's Used:
- HTML/CSS with Bootstrap 3.1
- Flask-Login, SQLAlchemy, WTForms, and, of course, Flask with Python 3
- Gmail API to send registration email and reset password emails
6. Detailed Description of the project (No more than 500 words)
Delts Dine is an application that helps provide meal schedules, as well as RSVP and check-in systems for each member that establishes a meal counting/swipe standard procedure for meals. Not only does it show users what meals are being offered for each lunch and dinner, but it also shows who has RSVP'd and who has officially checked in for the meal (checking in is restricted to a specific time period for lunch and dinner and means that a user has gotten their food). Each time a user checks-in, Delts Dine makes sure that users have not exceeded their weekly meal allowance, as well as creates a unique link to show the chef that they checked-in. There are two levels of access for Delts Dine: a member and an administrator. Administrators are allowed to add meals to a given day, as well as add other admins to help them out. 
7. List of Controllers and their short description (No more than 50 words for each controller)
- Page Controllers: Render different templates for views (home, about, meals, as well as admin functions such as adding an admin and adding a meal)
- Meal Controllers: Focusing on meal entries in the Meal table of the database, these controllers offer POST and GET routes on specific meals, as well as toggling weeks to view for the meal schedules by getting all meals for the week-in-view.
- RSVP Controllers: RSVPs a member for a specific Meal, as well deletes RSVPs 
- CheckIn Controllers: Create a CheckIn entry for a member and a meal.
- Authentication Controllers: Manages authentication for login, logout, register, forgot password.
- Gmail Controllers: Uses the Gmail API helper functions (in Helper Function section of app.py) to send registration confirmation email from deltsdine@gmail.com, as well as a link to reset password
8. List of Views and their short description (No more than 50 words for each view)
- Home: Landing page for deltsdine.herokuapp.com and either tells the user to login if they haven't already, or welcomes them.
- About: Quick about the application page.
- Meals: Gives authenticated members a weekly schedule of meals for lunch and dinners. Users can toggle which weeks they would like to view, as well as click into any meal to view what members have RSVP'd and checked-in for that specific meal.
- Add Meal: Simple form using WTForms that gets the title/description of the meal, as well as the date and whether or not it is for dinner. This form verifies that this date and time is not already populated with another meal.
- Add Admin: WTForms select dropdown that allows for an administrator to add another one by selecting another member in the Member table.
9. List of Tables, their Structure and short description
### Meal

| MealId (PK) | Date | Description | DinnerBool |
|:-----------: | :--: | :---------: | :--------: |
| Unique serial integer for Meal | Date of the meal | Title or description of meal | Whether or not meal is for dinner

### Member 

| Email (PK) | FirstName | LastName | MealAllowance | WeeksMealsUsed | Active | ConfirmedEmail | _Password | IsAdmin |
| :--------: | :--------: | :------: | :-----------: | :------------: | :----: | :-----------: | :-------: | :-----: |
| Unique email for each user | First name of user | Last name of user | Weekly meal plan number | Not used currently, due to dynamically calc. meals checked in for in a week | Whether or not user is an active member | Email was confirmed by Gmail API-sent email | Password hashed at rest | If user has administrative rights |

### RSVP

| MealId (PK, FK) | Email (PK, FK) | Timestamp |
|:-----------: | :--: | :---------: |
| MealId linked to a Meal entry | Email linked to a Member entry | Time of RSVP for records

### CheckIn
| MealId (PK, FK) | Email (PK, FK) | Timestamp |
|:-----------: | :--: | :---------: |
| MealId linked to a Meal entry | Email linked to a Member entry | Time of CheckIn for records

10. References/Resources: List all the references, resources or the online templates that were used for the project.
- [Template Structure of Flask application with Bootstrap, SQLAlchemy, and WTForms](https://github.com/realpython/flask-boilerplate)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/13/index.html)
- [Flask-Login User Handling Docs](https://exploreflask.com/en/latest/users.html)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [How to Send Emails on Behalf of Application Account](https://blog.mailtrap.io/send-emails-with-gmail-api/#How_to_make_your_app_send_emails_with_Gmail_API)
- [Medium Article by Dushan Kumarasinghe: Create a web application with python + Flask + PostgreSQL and deploy on Heroku ](https://medium.com/@dushan14/create-a-web-application-with-python-flask-postgresql-and-deploy-on-heroku-243d548335cc)
