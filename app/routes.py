from flask import render_template, flash, redirect, url_for
from app import app, db

#login functionality
from app.forms import LoginForm, RegistrationForm

#user functionality
from flask_login import current_user, login_user, logout_user
from app.models import User, Item

#homepage
@app.route('/')
@app.route('/index')
def index():

    return render_template('index.html', title="Front Page", featured=Item.query.filter_by(featured=True))

#login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data) or (user.usertype != form.usertype.data and user.usertype != 'Admin'):
            flash('No such user exists.', 'error')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember.data)
        return redirect(url_for('index'))
    return render_template('login.html', title="Login Page", form=form)

#logout page
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

#register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, usertype=form.usertype.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login')) 
    return render_template('register.html', title='Register', form=form)

#product page routing
@app.route('/product/<pid>')
def product(pid):
    if Item.query.filter_by(id=pid).first():
        item = Item.query.get(pid)
        return render_template('product.html', item=item)

    else:
        return render_template('404.html')

#vendor page
@app.route('/vendor/<username>')
def vendor(username):
    if User.query.filter_by(username=username).first():
        vendor = User.query.filter_by(username=username).first()
        return render_template('vendor.html', vendor=vendor)
    