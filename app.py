import os
from io import BytesIO
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, current_user, logout_user, login_required
)
from werkzeug.security import generate_password_hash, check_password_hash
import base64
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, cast
from sqlalchemy.types import String
from flask_migrate import Migrate
from forms import LoginForm, SignupForm, AddItemForm, SearchForm, LogoutForm, DeleteForm
from models import db, User, Item, generate_thumbnail
from dotenv import load_dotenv
from PIL import UnidentifiedImageError
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Security measures for session cookies
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False  # Set to True if using HTTPS
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/generate_pdf')
def generate_pdf():
    # Create a bytes buffer for the PDF data
    buffer = BytesIO()

    # Create a new PDF canvas
    c = canvas.Canvas(buffer, pagesize=A4)

    # Add logo image to the PDF (adjust the path as needed)
    logo_path = os.path.join(app.root_path, 'static/images/Logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 40, 750, width=100, height=50)  # Position the image on the page
    else:
        c.drawString(40, 750, "Logo not found")  # If logo is not found, show a message

    # Set the title for the PDF
    c.setFont("Helvetica", 16)
    c.drawString(40, 700, "Catalog of Items")

    # Get items from the database (for demo purposes, replace with your data fetching logic)
    items = Item.query.all()

    # Set the y position for the first item
    y_position = 650

    # Loop through the items and add them to the PDF
    for index, item in enumerate(items, start=1):
        if y_position < 100:  # Create a new page if we're running out of space
            c.showPage()
            y_position = 750

        # Add the item image if available (in high quality)
        if item.photo:
            item_img_path = os.path.join(app.root_path, 'static/images/', f"item_{item.id}.png")
            with open(item_img_path, 'wb') as img_file:
                img_file.write(item.photo)  # Save the image file temporarily
            c.drawImage(item_img_path, 40, y_position - 50, width=80, height=80)
            os.remove(item_img_path)  # Delete the temp image after it's added to the PDF

        # Add the item details in a table-like format
        c.setFont("Helvetica", 12)
        c.drawString(150, y_position, f"Item: {item.name}")
        c.drawString(150, y_position - 15, f"Article Number: {item.article_number}")
        c.drawString(150, y_position - 30, f"Size: {item.size_in_mm} mm")
        c.drawString(150, y_position - 45, f"Weight: {item.weight_in_g} g")

        # Move y_position up for the next item
        y_position -= 100

    # Save the PDF
    c.save()

    # Move the buffer position to the beginning
    buffer.seek(0)

    # Return the PDF as a response
    return send_file(buffer, as_attachment=True, download_name="catalog.pdf", mimetype='application/pdf')
@app.route('/')
@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    
    # Use paginate to get the pagination object
    pagination = Item.query.paginate(page, 20, False)
    
    # Extract the items from the pagination object
    items = pagination.items

    items_with_base64_images = [
        {
            'id': item.id,
            'article_number': item.article_number,
            'name': item.name,
            'size_in_mm': item.size_in_mm,
            'weight_in_g': item.weight_in_g,
            'photo': base64.b64encode(item.photo).decode('utf-8') if item.photo else None,
            'thumbnail': base64.b64encode(item.thumbnail).decode('utf-8') if item.thumbnail else None
        }
        for item in items
    ]

    # Pass the pagination object to the template as well
    return render_template('home.html', items=items_with_base64_images, pagination=pagination)

@app.context_processor
def inject_logout_form():
    return dict(logout_form=LogoutForm())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(
            form.password.data, method='pbkdf2:sha256'
        )
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    delete_form = DeleteForm()
    page = request.args.get('page', 1, type=int)

    if form.validate_on_submit():
        search_term = form.search_term.data

        # Create search criteria for multiple fields, casting numeric fields to string for matching
        search_criteria = or_(
            Item.name.ilike(f"%{search_term}%"),
            Item.article_number.ilike(f"%{search_term}%"),
            cast(Item.size_in_mm, String).ilike(f"%{search_term}%"),  # Cast numeric field to string for ILIKE
            cast(Item.weight_in_g, String).ilike(f"%{search_term}%")  # Cast numeric field to string for ILIKE
        )

        # Perform search with search criteria and include the 'photo' field in the query
        pagination = db.session.query(Item.id, Item.article_number, Item.name, Item.size_in_mm, Item.weight_in_g, Item.thumbnail, Item.photo).filter(search_criteria).paginate(page, 20, False)
    else:
        # Display all items if no search term is provided
        pagination = db.session.query(Item.id, Item.article_number, Item.name, Item.size_in_mm, Item.weight_in_g, Item.thumbnail, Item.photo).paginate(page, 20, False)

    items = pagination.items

    # Prepare base64-encoded images and send to the template
    items_with_base64_images = [
        {
            'id': item.id,
            'article_number': item.article_number,
            'name': item.name,
            'size_in_mm': item.size_in_mm,
            'weight_in_g': item.weight_in_g,
            'photo': base64.b64encode(item.photo).decode('utf-8') if item.photo else None,  # Add the full photo
            'thumbnail': base64.b64encode(item.thumbnail).decode('utf-8') if item.thumbnail else None
        }
        for item in items
    ]

    return render_template(
        'search.html',
        form=form,
        items=items_with_base64_images,
        delete_form=delete_form,
        pagination=pagination
    )




@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_data():
    form = AddItemForm()
    if form.validate_on_submit():
        article_number = form.article_number.data
        name = form.name.data
        size_in_mm = form.size_in_mm.data
        weight_in_g = form.weight_in_g.data
        photo_file = form.photo.data
        photo = photo_file.read()

        # Check if the article number already exists
        if Item.query.filter_by(article_number=article_number).first():
            flash('Article number already exists. Please use a different article number.', 'danger')
            return render_template('add_data.html', form=form)

        # Generate thumbnail
        try:
            thumbnail = generate_thumbnail(photo)
        except UnidentifiedImageError as e:
            flash(f'Invalid image format: {e}. Please upload a valid image file.', 'danger')
            return render_template('add_data.html', form=form)

        new_item = Item(
            article_number=article_number,
            name=name,
            size_in_mm=size_in_mm,
            weight_in_g=weight_in_g,
            photo=photo,
            thumbnail=thumbnail
        )
        db.session.add(new_item)
        try:
            db.session.commit()
            flash('Item added successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Article number already exists. Please use a different article number.', 'danger')
        return redirect(url_for('add_data'))  # Stay on the same page
    return render_template('add_data.html', form=form)

@app.route('/delete/<string:article_number>', methods=['POST'])
@login_required
def delete_item(article_number):
    # Your existing code
    item = Item.query.filter_by(article_number=article_number).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
    else:
        flash('Item not found!', 'danger')
    return redirect(url_for('search'))

@app.route('/api/check_article_number', methods=['POST'])
@login_required
def check_article_number():
    data = request.get_json()
    article_number = data.get('article_number')
    exists = (
        db.session.query(Item.article_number)
        .filter_by(article_number=article_number)
        .first()
        is not None
    )
    return jsonify({'exists': exists})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
