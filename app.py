from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from forms import LoginForm, SignupForm, AddDataForm, SearchForm
from models import db, User, Item

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def ensure_uploads_directory():
    uploads_path = os.path.join(app.static_folder, 'uploads')
    if not os.path.exists(uploads_path):
        os.makedirs(uploads_path)

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
        photo = None
        if form.photo.data:
            ensure_uploads_directory()  # Ensure the uploads directory exists
            photo_file = secure_filename(form.photo.data.filename)
            form.photo.data.save(os.path.join(app.static_folder, 'uploads', photo_file))
            photo = photo_file
        new_item = Item(name=form.name.data, article_number=form.article_number.data,
                        quantity=form.quantity.data, weight=form.weight.data, photo=photo)
        db.session.add(new_item)
        db.session.commit()
        flash('Data Added Successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('add_data.html', form=form)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    items = []
    if form.validate_on_submit():
        search_term = form.search_term.data
        items = Item.query.filter(Item.name.contains(search_term)).all()
    return render_template('search.html', form=form, items=items)

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists(os.path.join(app.instance_path, 'app.db')):
            os.makedirs(os.path.join(app.instance_path), exist_ok=True)
            db.create_all()
    app.run(debug=True)
