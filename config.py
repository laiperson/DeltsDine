import os

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Secret key for session management. You can generate random strings here:
# https://randomkeygen.com/
SECRET_KEY = 'my precious'

# Connect to the database
SQLALCHEMY_DATABASE_URI = 'postgres://dlfgkysocphbij:30562d0cab83a99010c26e07b3dd607c293af274dd147514fd7cc5b62e071787@ec2-174-129-254-220.compute-1.amazonaws.com:5432/d77fmc799mmovm'