from flask import render_template, request, Blueprint, redirect, url_for, flash, abort
from flask_login import current_user
from flaskblog import stripe_keys, api_logger, users_logger, db
from flaskblog.models import Post
from flask_csp.csp import csp_header
import stripe

main = Blueprint('main', __name__)

@main.after_request
def add_security_headers(resp):
    resp.headers['Content-Security-Policy']="script-src 'self'; script-src-elem https://checkout.stripe.com/checkout.js"
    return resp



@main.route("/")
@main.route("/home")
@csp_header({'script-src':"'self'"})
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('main/home.html', posts=posts)


@main.route("/about")
def about():
    return render_template('main/about.html', title='About')


@main.route("/plans")
def plans():
    return render_template('main/plans.html', title='Plans')


@main.route("/plans/get-premium", methods=["GET","POST"])
def get_premium():
    if not current_user.is_authenticated:
        flash("Please login or register first.", "info")
        return redirect(url_for('users.login'))
    if current_user.is_premium == True:
        flash("You have already purchased premium plan!")
        return redirect(url_for('mian.home'))
    return render_template('main/get-premium.html', title='Get Premium', key=stripe_keys['publishable_key'])


@main.route("/charge", methods=["POST"])
def charge_premium():
    if not current_user.is_authenticated:
        flash("Please login or register first.", "info")
        return redirect(url_for('users.login'))
    if current_user.is_premium == True:
        flash("You have already purchased premium plan!")
        return redirect(url_for('mian.home'))
    try:
        amount = 2000
        customer = stripe.Customer.create(
            email=current_user.email,
            source=request.form['stripeToken']
        )
        charge = stripe.Charge.create(
            customer=customer.id,
            amount=amount,
            currency='sgd',
            description='Premium Plan Purchase'
        )
    except Exception as e:
        api_logger.critical(e)
        abort(500)
    api_logger.info(f"Stripe payment successful: {current_user.username}")
    users_logger.info(f"Purchased premium plan: {current_user.username}")
    current_user.is_premium = True
    db.session.commit()
    flash('Thank you, you paid $20.00! Enjoy Premium!', 'success')
    return redirect(url_for('main.home'))
