import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import base64
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate
from forms import LoginForm, SignupForm, AddDataForm, SearchForm
from models import db, User, Item
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')

# Use PostgreSQL for local development and production
db_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/your_local_db_name')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def home():
    return render_template('home.html')

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
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_data():
    form = AddDataForm()
    if form.validate_on_submit():
        photo_base64 = None
        if form.photo.data:
            photo_data = form.photo.data.read()
            photo_base64 = base64.b64encode(photo_data).decode('utf-8')
        new_item = Item(
            article_number=form.article_number.data,
            name=form.name.data,
            size_in_inches=form.size_in_inches.data,
            weight=form.weight.data,
            photo=photo_base64
        )
        try:
            db.session.add(new_item)
            db.session.commit()
            flash('Data Added Successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Article number already exists. Please use a unique article number.', 'danger')
        return redirect(url_for('add_data'))
    return render_template('add_data.html', form=form)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    items = Item.query.all()  # Fetch all items initially
    if form.validate_on_submit():
        search_term = form.search_term.data
        items = Item.query.filter(Item.article_number.contains(search_term)).all()
    return render_template('search.html', form=form, items=items)

@app.route('/delete/<string:article_number>', methods=['POST'])
@login_required
def delete_item(article_number):
    item = Item.query.filter_by(article_number=article_number).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Item Deleted Successfully!', 'success')
    else:
        flash('Item not found!', 'danger')
    return redirect(url_for('search'))

@app.route('/api/check_article_number', methods=['POST'])
@login_required
def check_article_number():
    data = request.get_json()
    article_number = data.get('article_number')
    exists = db.session.query(Item.article_number).filter_by(article_number=article_number).first() is not None
    return jsonify({'exists': exists})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
