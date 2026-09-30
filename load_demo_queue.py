from app import app
from database.models import Student, ServicePoint
from database.database import db
from services.queue_engine import QueueEngine

def load_queue(count=8, service_point_id=1):
    with app.app_context():
        for i in range(count):
            student = Student(anonymous_identifier=f"LIVE-DEMO-{i+1}-{__import__('time').time_ns()}")
            db.session.add(student)
            db.session.flush()
            QueueEngine.join_queue(student.id, service_point_id)
        print(f"Added {count} live demo students to service point {service_point_id}.")

if __name__ == "__main__":
    load_queue()
