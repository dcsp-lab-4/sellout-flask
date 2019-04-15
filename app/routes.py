from flask import render_template, flash, redirect, url_for, request, g
from flask_uploads import UploadSet, configure_uploads, IMAGES
from app import app, db

#login functionality
from app.forms import LoginForm, RegistrationForm, AddToCartForm, CartQuantitiesForm, SearchForm, ItemForm

#user functionality
from flask_login import current_user, login_user, logout_user
from app.models import User, Item, Cart, CartItem, Order

#add_item Upload Configurations 
photos = UploadSet('photos',IMAGES)
configure_uploads(app,photos)

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

        #this fails if:
        ##the user doesnt exist
        ##the password is wrong (check_password)
        ##the selected usertype is wrong (want users to always know what they're logging in as, even if it's redundant)
        ##the usertype selection doesn't matter if you're logging in as an admin though
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
            address=form.address.data,
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
        if request.method == 'POST' and not request.args.get('featuring'):
            current_user.cart.add_item(item)
            flash('Add to cart successful.')
            return redirect(url_for('cart')) 
        elif request.args.get('featuring'):
            if item.toggle_feature():
                flash('Item featured successfully.')
            else:
                flash('Item removed from featured items successfully.')
            return redirect(url_for('index'))
        
        vendorname = item.vendor.firstname + " " + item.vendor.lastname
        photourl = photos.url(item.image)
        return render_template('product.html', item=item, form=form, vendorname=vendorname, photourl=photourl)

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

@app.route('/cart/checkout', methods=['GET','POST'])
def checkout():
    if not current_user.is_anonymous and current_user.usertype=='Customer':
        cart = Cart.query.filter_by(customerid=current_user.id).first()
        cartitems = CartItem.query.filter_by(cartid=cart.id)
        if cartitems:
            error_str = 'Vendor does not have enough items to fulfill order for:'
            errors = 0
            for cartitem in cartitems:
                if cartitem.quantity >= cartitem.item.stock:
                    error_str += 'cartitem.item.title\n'
                    errors += 1

        else:
            error_str += 'Cart is empty.'
            errors += 1

        if errors > 0:
            flash(error_str, 'error')
            return redirect(url_for('cart'))
        
        else:
            cart.checkout()
            flash('Purchase successful. Vendors have been notified.')
            return redirect(url_for('index'))
    
    else:
        return redirect(url_for('index'))


@app.route('/search')
def search():
    if not g.search_form.validate():
        return redirect(url_for('index'))
    items, total = Item.search(g.search_form.query.data, 1, 10)
    
    return render_template('search.html', items=items)

##vendor stuff
#add_item page
@app.route('/add_item',methods=["GET","POST"])
def add_item():
        form = ItemForm()
        if request.method == 'POST' and request.files and 'photo' in request.files and form.validate_on_submit():
            filename = photos.save(request.files['photo'])
            #url = photos.url(filename)
            item = Item(title=form.name.data,
                price=form.price.data,
                description=form.description.data,
                stock=form.stock.data,
                vendorid=current_user.id,
                image=filename)
            db.session.add(item)
            db.session.commit()
            flash("Congratulations, your item has been added")
            return redirect(url_for('inventory',username=current_user.username))
        else:
            return render_template('add_item.html', title="Add Item", form=form)

#inventory page
@app.route('/inventory',methods=["GET"])
def inventory():
    if not current_user.is_anonymous and current_user.usertype == 'Vendor':
        items = Item.query.filter_by(vendorid = current_user.id).all()
        if request.args.get('removed'):
            flash('Item removed from your inventory.')
            db.session.delete(Item.query.get(request.args.get('removed')))
            cartitems = CartItem.query.filter_by(itemid=request.args.get('removed'))
            for cartitem in cartitems:
                db.session.delete(cartitem)
            db.session.commit()
            return redirect(url_for('inventory'))
        return render_template('inventory.html',items = items)

##profile pages
#vendor page
@app.route('/vendor/<username>', methods=['GET', 'POST'])
def vendor(username):
    user = User.query.filter_by(username=username).first()
    if request.args.get('completed'):
        flash('Order marked as complete.')
        db.session.delete(Order.query.get(request.args.get('completed')))
        db.session.commit()

        return redirect(url_for('vendor', username=username))

    if user and user.usertype == 'Vendor':
        if current_user.username == user.username:
            orders = Order.query.filter_by(vendor=current_user)
            items = []
        else:
            orders = []
            items = Item.query.filter_by(vendor=user)

        return render_template('vendor.html', vendor=user, items=items, orders=orders)

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
            return render_template('admin.html', admin=user, users=User.query.all())
    
    else:
        return render_template('404.html')

