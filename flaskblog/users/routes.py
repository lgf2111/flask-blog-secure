from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from flaskblog import db, bcrypt, limiter, users_logger
from flaskblog.models import User, Post#, Role, UserRoles
from flaskblog.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                                   RequestResetForm, ResetPasswordForm)
from flaskblog.users.utils import save_picture, send_reset_email


users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        users_logger.info(f"User Registered: {user.username}")
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("You're already logged in!")
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # if not User.query.filter(User.email == 'member@example.com').first():
        #     user = User(
        #     email='member@example.com'
        # )
        # db.session.add(user)
        # db.session.commit() 
        # # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
        # if not User.query.filter(User.email == 'admin@example.com').first():
        #     user = User(
        #         email='admin@example.com'
        #     )
        #     user.roles.append(Role(name='Admin'))
        #     user.roles.append(Role(name='Agent'))
        #     db.session.add(user)
        #     db.session.commit()
        if user.login_attempt > 10:
            flash('Your account has been locked.', 'danger')
            if user.login_attempt <= 15:
                users_logger.warning(f"Login Attempt {user.login_attempt} (Locked): {user.username}")
            else:
                users_logger.error(f"Login Attempt {user.login_attempt} (Locked): {user.username}")
        elif user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                users_logger.info(f"Login Attempt {user.login_attempt} (Successful): {user.username}")
                user.login_attempt = 0
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            user.login_attempt += 1
            db.session.commit()
            flash('Login Unsuccessful. Please check email and password', 'danger')
            users_logger.warning(f"Login Attempt {user.login_attempt} (Unuccessful): {user.username}")
    return render_template('login.html', title='Login', form=form)


@users.route("/logout")
def logout():
    username = current_user.username
    logout_user()
    users_logger.info(f"User Logged Out: {username}")
    return redirect(url_for('main.home'))


@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        users_logger.info(f'User Account Updated: {current_user.username}')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        link = send_reset_email(user)
        users_logger.info(f"Password Reset Request: {user.username}, {link}")
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        user.login_attempt = 0
        db.session.commit()
        users_logger.info(f"Password Resetted: {user.username}")
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@users.route('/admin')
@login_required
# @roles_required('Admin')
def admin():
    return render_template('index.html')
