from app import db
from app.models import User, Item, Cart, CartItem

db.drop_all()
db.create_all()

test_users = [
    User(username='bob', email='bob@gmail.com', usertype='Customer', firstname='Robert', lastname='Yang', phone='1111111111', address='123 Fourth St Starkville MS'),
    User(username='amazon', email='amazon@gmail.com', usertype='Vendor', firstname='Amazon', lastname='Inc', phone='5555555555', address='403 Fourth St Starkville MS'),
    User(username='david', email='david@gmail.com', usertype='Admin', firstname='David', lastname='Lewis', phone='2222222222', address='404 Fourth St Starkville MS'),
    User(username='jenna', email='jenna@gmail.com', usertype='Vendor', firstname='Jenna', lastname='Jones', phone='1234567890', address='500 Fourth St Starkville MS'),
    User(username='lauren', email='lauren@gmail.com', usertype='Customer', firstname='Lauren', lastname='Smith', phone='5234567890', address='100 Fourth St Starkville MS')
]

test_items = [
    Item(title='Keyboard', description='A normal keyboard.', vendor=test_users[3], price=15.00, stock=43, featured=True, image='keyboard.jpg'),
    Item(title='Mouse', description='A normal mouse.', vendor=test_users[1], price=10.00, stock=12, featured=True, image='mouse.jpg'),
    Item(title='Shirt', description="It's a shirt.", vendor=test_users[1], price=15.00, stock=107, featured=False, image='shirt.jpg'),
    Item(title='Pants', description="It's pants.", vendor=test_users[1], price=15.00, stock=107, featured=True, image='pants.jpg'),
    Item(title='Hat', description="It's a hat.", vendor=test_users[3], price=15.00, stock=100, featured=True, image='hat.jpg'),
    Item(title='Shoes', description="It's shoes.", vendor=test_users[1], price=10.00, stock=107, featured=False, image='shoes.jpg'),
    Item(title='Computer', description="It's a computer.", vendor=test_users[3], price=500.00, stock=107, featured=True, image='computer.jpg'),
    Item(title='Shirt', description="It's another shirt.", vendor=test_users[1], price=15.00, stock=107, featured=True, image='shirt.jpg')
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