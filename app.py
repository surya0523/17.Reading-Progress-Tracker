from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, Book
from forms import RegisterForm, LoginForm, BookForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reading.db'

db.init_app(app)
with app.app_context():
    db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            session['last_book'] = None
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Login failed.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You've been logged out.", 'info')
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = BookForm()
    if form.validate_on_submit():
        book = Book(
            title=form.title.data,
            total_pages=form.total_pages.data,
            pages_read=form.pages_read.data,
            user_id=current_user.id
        )
        db.session.add(book)
        db.session.commit()
        session['last_book'] = form.title.data
        flash('Book progress saved!', 'success')
        return redirect(url_for('dashboard'))

    books = Book.query.filter_by(user_id=current_user.id).all()
    last_book = session.get('last_book')
    return render_template('dashboard.html', form=form, books=books, last=last_book)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    if book.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))
    form = BookForm(obj=book)
    if form.validate_on_submit():
        book.title = form.title.data
        book.total_pages = form.total_pages.data
        book.pages_read = form.pages_read.data
        db.session.commit()
        session['last_book'] = form.title.data
        flash('Book updated.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_book.html', form=form)
if __name__ == '__main__':
    app.run(debug=True)