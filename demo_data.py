from datetime import datetime, timedelta
import random
from app import app
from database.database import db
from database.models import Student, ServicePoint, Counter, QueueEntry, QueueEvent, ServiceRecord

def create_demo_history(service_point_id=1, days=3, samples_per_day=30):
    with app.app_context():
        point = ServicePoint.query.get(service_point_id)
        if not point:
            raise ValueError("Seed the database first")
        counter = Counter.query.filter_by(service_point_id=service_point_id).first()
        for day in range(days):
            base = datetime.utcnow() - timedelta(days=day + 1)
            for i in range(samples_per_day):
                student = Student(anonymous_identifier=f"DEMO-{day}-{i}-{random.randint(100,999)}")
                db.session.add(student)
                db.session.flush()
                joined = base + timedelta(minutes=i * 15)
                called = joined + timedelta(minutes=random.uniform(1, 8))
                duration = random.uniform(1.5, 5.5)
                completed = called + timedelta(minutes=duration)
                token = f"H-{day}-{i:03d}"
                entry = QueueEntry(token=token, student_id=student.id, service_point_id=service_point_id,
                                   status="COMPLETED", joined_at=joined, called_at=called,
                                   completed_at=completed, actual_wait=(called-joined).total_seconds()/60)
                db.session.add(entry)
                db.session.flush()
                db.session.add(ServiceRecord(queue_entry_id=entry.id, counter_id=counter.id,
                                             service_start=called, service_end=completed,
                                             service_duration=duration))
                db.session.add(QueueEvent(service_point_id=service_point_id, token=token,
                                          event_type="JOINED", timestamp=joined))
                db.session.add(QueueEvent(service_point_id=service_point_id, token=token,
                                          event_type="COMPLETED", timestamp=completed))
        db.session.commit()
        print(f"Added {days * samples_per_day} historical service records.")

if __name__ == "__main__":
    create_demo_history()
