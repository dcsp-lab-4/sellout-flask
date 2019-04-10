from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))
    phone = db.Column(db.String(16))
    usertype = db.Column(db.String(16))
    address = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    items = db.relationship('Item', backref='vendor', lazy='dynamic')
    cart = db.relationship('Cart', uselist=False, back_populates='customer')

    def initialize_cart(self):
        newcart = Cart(customer=self, price=0.0)
        db.session.add(newcart)
        db.session.commit()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}: {} {}>'.format(self.username, self.firstname, self.lastname)   

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.String(300))
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)
    featured = db.Column(db.Boolean)
    vendorid = db.Column(db.Integer, db.ForeignKey('user.id'))
    cartitem = db.relationship('CartItem', backref='item', lazy='dynamic')

    def __repr__(self):
        return '<Item {} sold by {}>'.format(self.title, User.query.get(self.vendorid).username)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customerid = db.Column(db.Integer, db.ForeignKey('user.id'))
    customer = db.relationship('User', back_populates='cart')
    price = db.Column(db.Float)
    items = db.relationship('CartItem', backref='cart', lazy='dynamic')

    def add_item(self, item):
        cartitem = CartItem.query.filter_by(cartid=self.id, itemid=item.id).first()
        if cartitem:
            cartitem.quantity += 1
        else:
            db.session.add(CartItem(cart=self, item=item, quantity=1))
        
        self.price += item.price
        
        db.session.commit()

    def set_quantity(self, item, quantity):
        cartitem = CartItem.query.filter_by(cartid=self.id, itemid=item.id).first()
        if cartitem:
            self.price -= cartitem.quantity * cartitem.item.price
            cartitem.quantity = quantity
            self.price += quantity
            db.session.commit()

    def remove_item(self, item):
        cartitem = CartItem.query.filter_by(cartid=self.id, itemid=item.id).first()
        if cartitem:
            self.price -= cartitem.quantity * cartitem.item.price
            db.session.delete(cartitem)
            db.session.commit()


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer)
    itemid = db.Column(db.Integer, db.ForeignKey('item.id'))
    cartid = db.Column(db.Integer, db.ForeignKey('cart.id'))

@login.user_loader
def load_user(id):
    return User.query.get(int(id))