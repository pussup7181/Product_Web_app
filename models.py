from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Item(db.Model):
    article_number = db.Column(db.String(100), primary_key=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    size_in_inches = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    photo = db.Column(db.Text, nullable=True)  # To store base64-encoded image
