from flask import Flask, render_template, redirect, request, url_for, flash
from flask_bootstrap import Bootstrap
import stripe
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from forms import RegistrationForm, LoginForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps
from flask import abort

stripe.api_key = 'sk_test_51MgZgULMezHay0pYBXNXx3oxtSZz9onHqOqoKAsL2VIYwWOdnCLd653pgjaNeAWoZRqyWkG7bgEixDGDVUhOCqHg00N5B0df8V'

products = stripe.Product.list(limit=8)["data"]

app = Flask(__name__)
app.app_context().push()


app.config['SECRET_KEY'] = "fdasfgfsdfisdhjnk;glbm75derfw4afsd54f"
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

YOUR_DOMAIN = 'http://localhost:5000'

cart = []
cart_prices = []

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100),unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def logged_in(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('register'))
    return decorated_func


@app.route('/')
def home():
    prices = []
    for item in products:
        curr_price = stripe.Price.retrieve(item.default_price)['unit_amount']
        price = round(curr_price / 100)
        prices.append(price)
    return render_template("index.html", products=products, prices=prices, cart=len(cart))


@app.route('/cart', methods=['GET'])
def cart_preview():
    cart_ids = []
    prices = []
    qtys = []
    cart_to_show = []
    total = 0
    for item in cart:
        cart_ids.append(item.id)
        if item in cart_to_show:
            pass
        else:
            cart_to_show.append(item)
    for item in products:
        curr_price = stripe.Price.retrieve(item.default_price)['unit_amount']
        price = round(curr_price / 100)
        prices.append(price)
        qty = cart_ids.count(item.id)
        qtys.append(qty)
    return render_template("cart.html", cart_to_show=cart_to_show, products=products, prices=prices, qtys=qtys, cart=len(cart))


@app.route('/product/<int:item_id>', methods=['GET'])
def show_item(item_id):
    prices = []
    for item in products:
        curr_price = stripe.Price.retrieve(item.default_price)['unit_amount']
        price = round(curr_price / 100)
        prices.append(price)
    requested_item = products[item_id]
    return render_template("item.html", products=products, prices=prices, item=requested_item, cart=len(cart))


@app.route('/add_to_cart/<int:item_id>', methods=['GET', 'POST'])
def add_to_cart(item_id):
    requested_item = products[item_id]
    cart.append(requested_item)
    return redirect(url_for('show_item', item_id=item_id))


@app.route('/remove_from_cart/<int:item_id>', methods=['GET', 'POST'])
def remove_from_cart(item_id):
    requested_item = cart[item_id]
    cart.remove(requested_item)
    return redirect(url_for('cart_preview', cart_to_show=cart, cart_prices=cart_prices, cart=len(cart)))


@app.route('/checkout', methods=['GET', 'POST'])
@logged_in
def create_checkout_session():
    cart_items = []
    cart_ids = []
    for item in cart:
        cart_ids.append(item.id)
    for item in cart:
        if {'price': item.default_price, 'quantity': cart_ids.count(item.id)} in cart_items:
            pass
        else:
            cart_items.append({'price': item.default_price,
                               'quantity': cart_ids.count(item.id)})
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=cart_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
        )

    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():

        if User.query.filter_by(email=form.email.data).first():
            #User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            password=form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            password=hash_and_salted_password,
            name=form.name.data,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form, cart=len(cart))

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated, cart=len(cart))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/cancel')
def cancel():
    return render_template("cancel.html", cart=len(cart))

@app.route('/success')
def success():
    return render_template("success.html", cart=len(cart))


if __name__ == '__main__':
    app.run(debug=True)