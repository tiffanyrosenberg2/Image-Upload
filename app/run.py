from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask import render_template
import os
from flask import jsonify

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'site.db')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Create the User class for database model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    hearts = db.relationship('Heart', backref='user', lazy=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Rendering navbar
@app.route('/navbar')
def navbar():
    return render_template('navbar.html')


# Create the Photo class for database model

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(100), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploader = db.relationship('User', backref='uploads', lazy=True)
    tags = db.relationship('Tag', backref='photo', lazy=True)
    hearts = db.relationship('Heart', backref='photo', lazy=True)

#Hearted photos
class Heart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)


# Create the Tag class for database model
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)

# Create the LoginForm class for handling login forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Create the RegistrationForm class for handling registration forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

# Create the SearchForm class for handling search forms
class SearchForm(FlaskForm):
    search_query = StringField('Search', validators=[DataRequired(), Length(min=1, max=50)])
    submit = SubmitField('Search')

# New route for handling the root URL '/'
@app.route('/')
def root():
    # Check if the user is logged in
    if current_user.is_authenticated:

        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

# Rendering login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=False)
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()

        if existing_user:
            flash('Username is already taken. Please choose a different one.', 'danger')
        else:
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')

    return render_template('register.html', form=form)

# rendering index/upload page
@app.route('/index')
@login_required
def index():
    flash_message = None
    return render_template('index.html',flash_message=flash_message)

#handling upload
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo.filename != '':
            photo_path = os.path.join('static/uploads', photo.filename)
            photo.save(photo_path)

            new_photo = Photo(filename=photo.filename, path=photo_path, uploader=current_user)

            tags = request.form.get('tags')
            if tags is not None:
                tag_list = [tag.strip() for tag in tags.split(',')]
                if not any(tag_list):
                    flash('At least 1 tag is required.', 'danger')
                    return redirect(url_for('index'))

                for tag_name in tag_list:
                    tag = Tag(name=tag_name, photo=new_photo)
                    db.session.add(tag)
                    print(f"Added tag: {tag_name} for photo: {new_photo.filename}")

                db.session.add(new_photo)
                db.session.commit()
                print(f"Added photo: {new_photo.filename} to the database")

                flash('Upload successful!', 'success')
                return redirect(url_for('index'))

    flash('No photo selected for upload.', 'danger')
    return redirect(url_for('index'))

#Search page
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    photos = []
    flash_message = None

    if form.validate_on_submit():
        search_query = form.search_query.data
        photos = Photo.query.filter(
            (Photo.tags.any(Tag.name.ilike(f"%{search_query}%"))) |
            (Photo.filename.ilike(f"%{search_query}%"))
        ).all()

        if not photos:
            flash_message = 'Unfortunately, no matching tag or image was found.'
        else:
            flash_message = f'Successfully found {len(photos)} photos for your search.'

    return render_template('search.html', photos=photos, form=form, flash_message=flash_message)

#heart photo
@app.route('/heart_photo/<int:photo_id>', methods=['POST'])
@login_required
def heart_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    user = current_user

    existing_heart = Heart.query.filter_by(user_id=user.id, photo_id=photo.id).first()

    if existing_heart:
        db.session.delete(existing_heart)
        db.session.commit()
        hearted = False
    else:
        new_heart = Heart(user=user, photo=photo)
        db.session.add(new_heart)
        db.session.commit()
        hearted = True

    return jsonify({'message': 'Hearted photo!', 'hearted': hearted})

# photo deletion
@app.route('/delete_photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)

    Tag.query.filter_by(photo_id=photo.id).delete()

    Heart.query.filter_by(photo_id=photo.id).delete()

    db.session.delete(photo)
    db.session.commit()

    return redirect(url_for('search'))

#Hearted images
@app.route('/hearted')
@login_required
def hearted():
   
    hearted_photos = Photo.query.join(Heart).filter(Heart.user_id == current_user.id).all()
    
    return render_template('hearted.html', hearted_photos=hearted_photos)

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)   

    app.run(debug=True)