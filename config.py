import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///local.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
