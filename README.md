1. Project Type: Plan A or B or C
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
- Meal (**PK** MealId, Date, Description, DinnerBool): unique serial integer for MealId, type date for Date of the meal, title or description of that meal, and whether or not it is for dinner on that day.
| PK MealId                      | Date             | Description                  | DinnerBool                        |
|--------------------------------|------------------|------------------------------|-----------------------------------|
| Unique serial integer for Meal | Date of the meal | Title or description of meal | Whether or not meal is for dinner |
- Member (**PK**Email, FirstName, LastName, MealALlowance, WeekMealsUsed, Active, ConfirmedEmail, _Password, IsAdmin): unique email for each user that must be verified, first and last name of the member, number of meals/swipes this member has, WeekMealsUsed is not being used due to dynamically calculating number of meals used in a given week, whether or not a user is active in the house, ConfirmedEmail is showing if they got the confirmation email and provided a valid email address, their password which is hashed at rest, and IsAdmin is updated to True if a user is given administrative rights.
10. References/Resources: List all the references, resources or the online templates that were used for the project.