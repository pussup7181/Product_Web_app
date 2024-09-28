from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from PIL import Image, UnidentifiedImageError
import io

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'  # Add this line
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_number = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    size_in_mm = db.Column(db.Float, nullable=False)
    weight_in_g = db.Column(db.Float, nullable=False)
    photo = db.Column(db.LargeBinary, nullable=True)
    thumbnail = db.Column(db.LargeBinary, nullable=True)

    def __repr__(self):
        return f"<Item {self.name}>"

def generate_thumbnail(image_data):
    if not image_data:
        raise UnidentifiedImageError("No image data provided.")
    image = Image.open(io.BytesIO(image_data))
    image.thumbnail((100, 100))  # Set the thumbnail size
    thumb_io = io.BytesIO()
    image.save(thumb_io, format='PNG')
    return thumb_io.getvalue()
