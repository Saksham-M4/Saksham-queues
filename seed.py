from app import app
from database.database import db
from database.models import Student, ServicePoint, Counter, MenuItem

def seed_database():
    with app.app_context():
        db.drop_all(); db.create_all()
        student=Student(anonymous_identifier='STUDENT001')
        canteen=ServicePoint(name='GCU Main Canteen',type='canteen',location='Garden City University',status='OPEN',created_by_email='unser01@gmail.com',is_active=True)
        db.session.add_all([student,canteen]); db.session.flush()
        db.session.add_all([
            Counter(service_point_id=canteen.id,counter_number=1,status='OPEN'),
            Counter(service_point_id=canteen.id,counter_number=2,status='OPEN'),
            Counter(service_point_id=canteen.id,counter_number=3,status='CLOSED'),
            MenuItem(service_point_id=canteen.id,name='Veg Burger',price=60,category='Quick Bites',stock_target=45),
            MenuItem(service_point_id=canteen.id,name='Paneer Roll',price=80,category='Meals',stock_target=35),
            MenuItem(service_point_id=canteen.id,name='French Fries',price=50,category='Sides',stock_target=40),
            MenuItem(service_point_id=canteen.id,name='Cold Coffee',price=70,category='Beverages',stock_target=30),
            MenuItem(service_point_id=canteen.id,name='Masala Dosa',price=65,category='Meals',stock_target=35),
        ])
        db.session.commit()
        print(f'Seeded: student={student.id}, service_point={canteen.id}, counters=3, menu=5')
if __name__=='__main__': seed_database()
