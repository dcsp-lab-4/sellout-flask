from app import db
from app.models import User, Item

db.drop_all()
db.create_all()

customer_ex = User(username='bob', email='bob@gmail.com', usertype='Customer', firstname='Robert', lastname='Yang')
vendor_ex = User(username='amazon', email='amazon@gmail.com', usertype='Vendor', firstname='Amazon', lastname='Inc')
admin_ex = User(username='david', email='david@gmail.com', usertype='Admin', firstname='David', lastname='Lewis')

db.session.add(customer_ex)
db.session.add(vendor_ex)
db.session.add(admin_ex)
db.session.commit()

results = User.query.all()
for u in results:
    print(u)

db.session.remove()
db.drop_all()