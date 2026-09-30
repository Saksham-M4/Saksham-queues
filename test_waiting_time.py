from app import app
from database.database import db
from database.models import ServicePoint, Counter
from services.waiting_time import WaitingTimeService

def run():
    with app.app_context():
        db.drop_all(); db.create_all()
        p = ServicePoint(name="Test Canteen", type="canteen", status="OPEN")
        db.session.add(p); db.session.flush()
        db.session.add_all([Counter(service_point_id=p.id, counter_number=1, status="OPEN"),
                            Counter(service_point_id=p.id, counter_number=2, status="OPEN")]); db.session.commit()
        assert WaitingTimeService.calculate_eta(p.id, 2) == 3.0
        print("PASS: ETA calculation")

if __name__ == "__main__": run()
