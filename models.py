from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Item(db.Model):
    article_number = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100))
    size_in_inches = db.Column(db.Float)
    weight = db.Column(db.Float)
    photo = db.Column(db.Text)  # Base64 encoded original image
    thumbnail = db.Column(db.Text)  # Base64 encoded compressed image

