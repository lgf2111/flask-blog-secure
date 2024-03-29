import os
import secrets
from PIL import Image
from datetime import datetime
from flask import url_for, current_app
from flask_mail import Message
from flaskblog import mail


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def send_reset_email(user):
    token = user.get_reset_token()
    link = url_for('users.reset_token', token=token, _external=True)
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f'To reset your password, visit the following link: {link}\n'\
                'If you did not make this request then simply ignore this email and no changes will be made.'
    mail.send(msg)
    return link


def send_alert_email(activity, user):
    msg = Message('Suspicious Activity Detected', sender='noreply@demo.com', recipients=['213587x@gmail.com'])
    msg.body = f"User {user.username} has tried to {activity} on {datetime.now()}.\n{url_for('admin.index', _external=True)}"
    mail.send(msg)
    
    msg = Message('Suspicious Activity Detected', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f"Someone has tried to {activity}, if this isn't you, please change your password.\n{url_for('users.reset_request', _external=True)}"
    mail.send(msg)

def send_mfa_email(user):
    token = user.get_mfa_token()
    link = url_for('users.mfa_token', token=token, _external=True)
    msg = Message('2FA Verification', sender='noreply@demo.com', recipients=[user.email])
    msg.body =  'This token will expire in 60 Seconds\n'\
                f'To verify, visit the following link: {link}\n'\
                'If you did not make this request then simply ignore this email.'
    mail.send(msg)
    return link
