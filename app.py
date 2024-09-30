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
from flask_migrate import Migrate
from forms import LoginForm, SignupForm, AddItemForm, SearchForm, LogoutForm, DeleteForm
from models import db, User, Item, generate_thumbnail
from dotenv import load_dotenv
from PIL import UnidentifiedImageError
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet

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
# Route for PDF generation
@app.route('/generate_pdf')
@login_required
def generate_pdf():
    items = Item.query.all()  # Fetch all items from the database

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []
    styles = getSampleStyleSheet()
    data = []

    # Define the header for the table
    header = ['Image', 'Details']
    data.append(header)

    # Loop through each item and add to the table data
    for item in items:
        # Convert the photo back to high-quality for the PDF
        if item.photo:
            img = Image(BytesIO(item.photo), width=2*inch, height=2*inch)
        else:
            img = "No Image Available"

        # Add item details as a string
        details = f"Name: {item.name}\nArticle Number: {item.article_number}\nSize: {item.size_in_mm} mm\nWeight: {item.weight_in_g} g"
        
        # Append image and details to the data
        data.append([img, details])

    # Create the table with the data
    table = Table(data, colWidths=[2.5 * inch, 4 * inch])

    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    
    # Build the PDF
    doc.build(elements)
    
    buffer.seek(0)
    
    # Send the PDF as response
    return send_file(buffer, as_attachment=True, download_name='items_catalog.pdf', mimetype='application/pdf')
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
        # Include photo in the selected fields
        pagination = db.session.query(Item.id, Item.article_number, Item.name, Item.size_in_mm, Item.weight_in_g, Item.thumbnail, Item.photo).filter(Item.name.ilike(f"%{search_term}%")).paginate(page, 20, False)
    else:
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
            'photo': base64.b64encode(item.photo).decode('utf-8') if item.photo else None,
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
