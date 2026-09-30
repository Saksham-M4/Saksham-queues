from datetime import datetime
from .database import db

class Student(db.Model):
    __tablename__='students'
    id=db.Column(db.Integer,primary_key=True)
    anonymous_identifier=db.Column(db.String(100),unique=True,nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

class ServicePoint(db.Model):
    __tablename__='service_points'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    type=db.Column(db.String(50),default='stall',nullable=False)
    location=db.Column(db.String(200))
    status=db.Column(db.String(20),default='OPEN',nullable=False)
    created_by_email=db.Column(db.String(200))
    is_active=db.Column(db.Boolean,default=True,nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

class Counter(db.Model):
    __tablename__='counters'
    id=db.Column(db.Integer,primary_key=True)
    service_point_id=db.Column(db.Integer,db.ForeignKey('service_points.id'),nullable=False)
    counter_number=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(20),default='OPEN',nullable=False)
    current_token=db.Column(db.String(20))
    opened_at=db.Column(db.DateTime,default=datetime.utcnow)
    closed_at=db.Column(db.DateTime)

class MenuItem(db.Model):
    __tablename__='menu_items'
    id=db.Column(db.Integer,primary_key=True)
    service_point_id=db.Column(db.Integer,db.ForeignKey('service_points.id'),nullable=False)
    name=db.Column(db.String(120),nullable=False)
    price=db.Column(db.Float,nullable=False)
    available=db.Column(db.Boolean,default=True,nullable=False)
    category=db.Column(db.String(80),default='Food')
    stock_target=db.Column(db.Integer,default=50,nullable=False)
    waste_count=db.Column(db.Integer,default=0,nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

class Order(db.Model):
    __tablename__='orders'
    id=db.Column(db.Integer,primary_key=True)
    order_number=db.Column(db.String(30),unique=True,nullable=False)
    student_id=db.Column(db.Integer,db.ForeignKey('students.id'),nullable=False)
    service_point_id=db.Column(db.Integer,db.ForeignKey('service_points.id'),nullable=False)
    queue_entry_id=db.Column(db.Integer,db.ForeignKey('queue_entries.id'))
    counter_id=db.Column(db.Integer,db.ForeignKey('counters.id'))
    status=db.Column(db.String(20),default='PLACED',nullable=False)
    total=db.Column(db.Float,default=0)
    eta_minutes=db.Column(db.Float,default=0)
    eta_at=db.Column(db.DateTime)
    admin_message=db.Column(db.String(500))
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    updated_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

class OrderItem(db.Model):
    __tablename__='order_items'
    id=db.Column(db.Integer,primary_key=True)
    order_id=db.Column(db.Integer,db.ForeignKey('orders.id'),nullable=False)
    menu_item_id=db.Column(db.Integer,db.ForeignKey('menu_items.id'),nullable=False)
    name=db.Column(db.String(120),nullable=False)
    price=db.Column(db.Float,nullable=False)
    quantity=db.Column(db.Integer,default=1,nullable=False)

class QueueEntry(db.Model):
    __tablename__='queue_entries'
    id=db.Column(db.Integer,primary_key=True)
    token=db.Column(db.String(20),unique=True,nullable=False)
    student_id=db.Column(db.Integer,db.ForeignKey('students.id'),nullable=False)
    service_point_id=db.Column(db.Integer,db.ForeignKey('service_points.id'),nullable=False)
    status=db.Column(db.String(20),default='WAITING',nullable=False)
    joined_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    called_at=db.Column(db.DateTime)
    completed_at=db.Column(db.DateTime)
    cancelled_at=db.Column(db.DateTime)
    estimated_wait=db.Column(db.Float,default=0)
    actual_wait=db.Column(db.Float)

class ServiceRecord(db.Model):
    __tablename__='service_records'
    id=db.Column(db.Integer,primary_key=True)
    queue_entry_id=db.Column(db.Integer,db.ForeignKey('queue_entries.id'),nullable=False)
    counter_id=db.Column(db.Integer,db.ForeignKey('counters.id'),nullable=False)
    service_start=db.Column(db.DateTime)
    service_end=db.Column(db.DateTime)
    service_duration=db.Column(db.Float)

class QueueEvent(db.Model):
    __tablename__='queue_events'
    id=db.Column(db.Integer,primary_key=True)
    service_point_id=db.Column(db.Integer,db.ForeignKey('service_points.id'),nullable=False)
    token=db.Column(db.String(20))
    event_type=db.Column(db.String(50),nullable=False)
    timestamp=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

class Prediction(db.Model):
    __tablename__='predictions'
    id=db.Column(db.Integer,primary_key=True)
    service_point_id=db.Column(db.Integer,db.ForeignKey('service_points.id'),nullable=False)
    timestamp=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    predicted_queue=db.Column(db.Float)
    predicted_wait=db.Column(db.Float)
    congestion=db.Column(db.String(20))
    confidence=db.Column(db.Float)

class Notification(db.Model):
    __tablename__='notifications'
    id=db.Column(db.Integer,primary_key=True)
    student_id=db.Column(db.Integer,db.ForeignKey('students.id'),nullable=False)
    type=db.Column(db.String(50),nullable=False)
    message=db.Column(db.String(500),nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    read=db.Column(db.Boolean,default=False,nullable=False)
