from app import db
from app.models import User, Item, Cart, CartItem

db.drop_all()
db.create_all()

test_users = [
    User(username='bob', email='bob@gmail.com', usertype='Customer', firstname='Robert', lastname='Yang'),
    User(username='amazon', email='amazon@gmail.com', usertype='Vendor', firstname='Amazon', lastname='Inc'),
    User(username='david', email='david@gmail.com', usertype='Admin', firstname='David', lastname='Lewis'),
    User(username='jenna', email='jenna@gmail.com', usertype='Vendor', firstname='Jenna', lastname='Jones'),
    User(username='lauren', email='lauren@gmail.com', usertype='Customer', firstname='Lauren', lastname='Smith')
]

test_items = [
    Item(title='Keyboard', description='A normal keyboard.', vendor=test_users[3], price=15.00, stock=43, featured=True),
    Item(title='Mouse', description='A normal mouse.', vendor=test_users[1], price=10.00, stock=12, featured=True),
    Item(title='Shirt', description="It's a shirt.", vendor=test_users[1], price=15.00, stock=107, featured=False),
    Item(title='Pants', description="It's pants.", vendor=test_users[1], price=15.00, stock=107, featured=True),
    Item(title='Hat', description="It's a hat.", vendor=test_users[3], price=15.00, stock=100, featured=True),
    Item(title='Shoes', description="It's shoes.", vendor=test_users[1], price=10.00, stock=107, featured=False),
    Item(title='Computer', description="It's a computer.", vendor=test_users[3], price=500.00, stock=107, featured=True),
    Item(title='Shirt', description="It's another shirt.", vendor=test_users[1], price=15.00, stock=107, featured=True)
]

for user in test_users:
    user.initialize_cart()
    user.set_password(user.username + '123')
    db.session.add(user)

for item in test_items:
    db.session.add(item)

bobcart = Cart.query.filter_by(customerid=1).first()
bobcart.add_item(Item.query.filter_by(id=2).first())

db.session.commit()

U = User.query.all()
for dbuser in U:
    print(dbuser)

I = Item.query.all()
for dbitem in I:
    print(dbitem)