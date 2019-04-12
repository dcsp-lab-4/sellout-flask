from flask import render_template, flash, redirect, url_for, request, g
from app import app, db

#login functionality
from app.forms import LoginForm, RegistrationForm, AddToCartForm, CartQuantitiesForm, SearchForm

#user functionality
from flask_login import current_user, login_user, logout_user
from app.models import User, Item, Cart, CartItem

#universal content rendering
@app.before_request
def before_request():
    g.search_form = SearchForm()

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

        if not user or not user.check_password(form.password.data) or (user.usertype != form.usertype.data and user.usertype != 'Admin'):
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
        user = User(username=form.username.data, 
            email=form.email.data, 
            phone=form.phone.data,
            firstname=form.firstname.data,
            lastname=form.lastname.data,
            usertype=form.usertype.data)
            
        user.set_password(form.password.data)
        user.initialize_cart()
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login')) 
    return render_template('register.html', title='Register', form=form)

#product page routing
@app.route('/product/<pid>', methods=['GET', 'POST'])
def product(pid):
    item = Item.query.filter_by(id=pid).first()
    if item:
        form = AddToCartForm()
        if request.method == 'POST':
            current_user.cart.add_item(item)
            flash('Add to cart successful.')
            return redirect(url_for('cart')) 
        return render_template('product.html', item=item, form=form)

    else:
        return render_template('404.html')

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if current_user.is_anonymous:
        flash('You must register to buy items!', 'error')
        return redirect(url_for('register')) 

    elif current_user.usertype == 'Vendor' or current_user.usertype == 'Admin':
        flash('You must be a customer to buy items!', 'error')
        return redirect(url_for('index'))

    else:
        editing = False
        form = None
        cart = Cart.query.filter_by(customerid=current_user.id).first()
        if request.args.get('removed'):
            flash('Item removed from cart.')
            cart.remove_item(Item.query.get(request.args.get('removed')))
            return redirect(url_for('cart'))

        cartitems = CartItem.query.filter_by(cartid=cart.id)

        if request.args.get('edit'):
            editing = True
            quantities = []
            for cartitem in cartitems:
                temp = {}
                temp["quantity"] = cartitem.quantity
                quantities.append(temp)
            form = CartQuantitiesForm(quantities=quantities)
        
        if form and request.method == 'POST':
            for i, cartitem in enumerate(cartitems):
                current_user.cart.set_quantity(cartitem.item, form.quantities[i].quantity.data)

            flash('Quantities saved.')
            return redirect(url_for('cart'))

        return render_template('cart.html', cartitems=cartitems, ccart=cart, editing=editing, form=form)

@app.route('/search')
def search():
    if not g.search_form.validate():
        return redirect(url_for('index'))
    items, total = Item.search(g.search_form.query.data, 1, 10)
    
    return render_template('search.html', items=items)

##profile pages
#vendor page
@app.route('/vendor/<username>')
def vendor(username):
    user = User.query.filter_by(username=username).first()
    if user and user.usertype == 'Vendor':
        return render_template('vendor.html', vendor=user)

    else:
        return render_template('404.html')

#customer page
@app.route('/user/<username>')
def customer(username):
    user = User.query.filter_by(username=username).first()
    if user and user.usertype == 'Customer':
        return render_template('customer.html', customer=user)

    else:
        return render_template('404.html')

#admin page
@app.route('/admin/<username>')
def admin(username):
    user = User.query.filter_by(username=username).first()
    if user and user.usertype == 'Admin':
        if current_user.is_anonymous or current_user.usertype != 'Admin':
            return render_template('403.html')
        
        else:
            return render_template('admin.html', admin=user)
    
    else:
        return render_template('404.html')

