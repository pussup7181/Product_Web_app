import os

class Config:
    SECRET_KEY = os.urandom(24)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:4561@localhost:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
