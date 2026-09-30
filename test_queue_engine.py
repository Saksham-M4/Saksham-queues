from app import app
from database.database import db
from database.models import Student, ServicePoint, Counter
from services.queue_engine import QueueEngine

def run():
    with app.app_context():
        db.drop_all(); db.create_all()
        s = Student(anonymous_identifier="TEST")
        p = ServicePoint(name="Test Canteen", type="canteen", status="OPEN")
        db.session.add_all([s, p]); db.session.flush()
        db.session.add(Counter(service_point_id=p.id, counter_number=1, status="OPEN")); db.session.commit()
        entry = QueueEngine.join_queue(s.id, p.id)
        assert QueueEngine.get_position(entry.id) == 1
        serving, reason = QueueEngine.serve_next(p.id, 1)
        assert reason == "OK" and serving.status == "SERVING"
        blocked, reason = QueueEngine.serve_next(p.id, 1)
        assert blocked is None and reason == "COUNTER_BUSY"
        QueueEngine.complete_service(entry.id)
        assert entry.status == "COMPLETED"
        print("PASS: queue engine + busy-counter protection")

if __name__ == "__main__": run()
