from app import db, login
from app.search import add_to_index, remove_from_index, query_index
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

#this is a mixin class that gives searchability with Elasticsearch
class SearchableMixin(object):
    '''
    When SearchableMixin is included for inheritance on another object, it is given 
    searchability in the Elasticsearch cluster. .reindex() must be called to initialize
    searchability on objects that are retroactively given SearchableMixin.
    '''
    
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0 or not len(ids):
            return cls.query.filter_by(id=0), 0
        
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        
        #return cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)), total
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        #figure out what the current db.session's state is
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }
    
    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(obj.__tablename__, obj)

#listen to SQLAlchemy commits so the elasticsearch indices are always updated on database changes
db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

class User(UserMixin, db.Model):
    '''
    All site users are included on this table.
    '''

    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(64), index=True, unique=True)
    email           = db.Column(db.String(120), index=True, unique=True)
    firstname       = db.Column(db.String(64))
    lastname        = db.Column(db.String(64))
    phone           = db.Column(db.String(16))
    usertype        = db.Column(db.String(16))
    address         = db.Column(db.String(64))
    password_hash   = db.Column(db.String(128))
    items           = db.relationship('Item', backref='vendor', lazy='dynamic')

    cart            = db.relationship('Cart', uselist=False, back_populates='customer')

    def initialize_cart(self):
        newcart = Cart(customer=self, cartprice=0.0)
        db.session.add(newcart)
        db.session.commit()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}: {} {}>'.format(self.username, self.firstname, self.lastname)   

class Item(SearchableMixin, db.Model):
    '''
    Item defines the table of products for sale. Item.vendor accesses the seller of an Item.
    '''

    __searchable__ = ['title', 'description']
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(64))
    description = db.Column(db.String(300))
    price       = db.Column(db.Float)
    stock       = db.Column(db.Integer)
    featured    = db.Column(db.Boolean)
    image       = db.Column(db.String(64))
    vendorid    = db.Column(db.Integer, db.ForeignKey('user.id'))
    cartitem    = db.relationship('CartItem', backref='item', lazy='dynamic')
    order       = db.relationship('Order', backref='item', lazy='dynamic')
    tags        = db.relationship('ItemTag', backref='item', lazy='dynamic')

    def toggle_feature(self):
        self.featured = not self.featured
        db.session.commit()
        return self.featured

    def __repr__(self):
        return '<Item {} sold by {}>'.format(self.title, User.query.get(self.vendorid).username)

#cart system models
class Cart(db.Model):
    '''
    Cart defines the table of carts in the database. Every customer has one Cart.
    A customer's Cart is accessible through the .cart attribute on a User of type 'Customer' 
    '''

    id          = db.Column(db.Integer, primary_key=True)
    customerid  = db.Column(db.Integer, db.ForeignKey('user.id'))
    customer    = db.relationship('User', back_populates='cart')
    cartprice   = db.Column(db.Float)
    items       = db.relationship('CartItem', backref='cart', lazy='dynamic')

    def add_item(self, item):
        '''
        Add Item >item< to cart. 
        '''
        
        cartitem = CartItem.query.filter_by(cartid=self.id, itemid=item.id).first()
        if cartitem:
            cartitem.quantity += 1
        else:
            db.session.add(CartItem(cart=self, item=item, quantity=1))

        db.session.commit()
        self.update_price()

    def set_quantity(self, item, quantity):
        '''
        Directly set a >quantity< of Item argument >item<. 
        Doesn't work if the Item is not found in the Cart.
        '''

        cartitem = CartItem.query.filter_by(cartid=self.id, itemid=item.id).first()
        if cartitem:
            if quantity <= 0:
                return self.remove_item(item)
            cartitem.quantity = quantity
            db.session.commit()
            self.update_price()

    def remove_item(self, item):
        '''
        Remove an item from the cart based on an Item passed as an argument, >item<.
        '''

        cartitem = CartItem.query.filter_by(cartid=self.id, itemid=item.id).first()
        if cartitem:
            db.session.delete(cartitem)
            db.session.commit()
            self.update_price()
        return True

    def update_price(self):
        '''
        Internal cart function. Call this whenever you change the cart's contents.
        Iterate over items in cart and compute price.
        '''

        cartitems = CartItem.query.filter_by(cartid=self.id)
        total_price = 0.0
        for cartitem in cartitems:
            total_price += cartitem.item.price * cartitem.quantity
        
        self.cartprice = total_price
        db.session.commit()

    def checkout(self):
        '''
        Perform managerial cart checkout tasks with this cart's items.
        Do NOT call this function unless the checkout is deemed valid elsewhere.
        No validation is done here. 
        '''

        cartitems = CartItem.query.filter_by(cartid=self.id)
        for cartitem in cartitems:
            db.session.add(Order(
                item=cartitem.item,
                quantity=cartitem.quantity,
                price=(cartitem.item.price*cartitem.quantity),
                customer=self.customer,
                vendor=cartitem.item.vendor,
                name=(self.customer.firstname+" "+self.customer.lastname),
                address=self.customer.address
            ))
            item = Item.query.get(cartitem.itemid)
            item.stock -= cartitem.quantity
            db.session.delete(cartitem)
        
        db.session.commit()
        self.update_price()
        


class CartItem(db.Model):
    '''
    Every time an item is added to a cart, a CartItem is added to the CartItems table.
    Entries in this table define a relationship between an Item and a Cart. 
    '''

    id          = db.Column(db.Integer, primary_key=True)
    quantity    = db.Column(db.Integer)
    itemid      = db.Column(db.Integer, db.ForeignKey('item.id'))
    cartid      = db.Column(db.Integer, db.ForeignKey('cart.id'))

class Order(db.Model):
    '''
    Whenever a Cart.checkout() is successfully completed, an Order is created for each CartItem.
    Vendors can see the list of Orders they've gotten on their profile page.
    '''

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(64))
    address         = db.Column(db.String(128))
    quantity        = db.Column(db.Integer)
    price           = db.Column(db.Float)
    itemid          = db.Column(db.Integer, db.ForeignKey('item.id'))
    customerid      = db.Column(db.Integer, db.ForeignKey('user.id'))
    vendorid        = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    customer        = db.relationship('User', foreign_keys=[customerid])
    vendor          = db.relationship('User', foreign_keys=[vendorid])

#tagging system models
class Tag(SearchableMixin, db.Model):
    '''
    Part of planned Tagging system. Currently unused.
    '''
    __searchable__ = ['title']
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(64), index=True, unique=True)
    itemtags    = db.relationship('ItemTag', backref='tag', lazy='dynamic')

class ItemTag(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    itemid  = db.Column(db.Integer, db.ForeignKey('item.id'))
    tagid   = db.Column(db.Integer, db.ForeignKey('tag.id'))


        

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

