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
    
def save_image(photo_file):
    image = Image.open(io.BytesIO(photo_file))
    
    # Resize image to maintain aspect ratio
    max_width = 800
    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height), Image.ANTIALIAS)

    # Convert to webp format
    webp_io = io.BytesIO()
    image.save(webp_io, format='WEBP', quality=80)  # Lowered quality to 80 for better compression
    return webp_io.getvalue()


def generate_thumbnail(image_data):
    if not image_data:
        raise UnidentifiedImageError("No image data provided.")
    image = Image.open(io.BytesIO(image_data))
    image.thumbnail((100, 100))  # Set the thumbnail size
    thumb_io = io.BytesIO()
    image.save(thumb_io, format='PNG')
    return thumb_io.getvalue()
