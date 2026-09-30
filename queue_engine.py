from datetime import datetime
from database.database import db
from database.models import QueueEntry, QueueEvent, Counter, ServiceRecord

class QueueEngine:
    @staticmethod
    def get_active_counters(service_point_id):
        return Counter.query.filter_by(service_point_id=service_point_id, status="OPEN").count()

    @staticmethod
    def get_busy_counters(service_point_id):
        return Counter.query.filter_by(service_point_id=service_point_id, status="BUSY").count()

    @staticmethod
    def get_queue(service_point_id):
        return (QueueEntry.query.filter_by(service_point_id=service_point_id, status="WAITING")
                .order_by(QueueEntry.joined_at.asc(), QueueEntry.id.asc()).all())

    @staticmethod
    def generate_token(service_point_id):
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"Q-{today}-"
        latest = QueueEntry.query.filter(QueueEntry.service_point_id == service_point_id,
                                         QueueEntry.token.like(prefix + "%"))\
            .order_by(QueueEntry.id.desc()).first()
        number = 1
        if latest:
            try:
                number = int(latest.token.split("-")[-1]) + 1
            except ValueError:
                number = QueueEntry.query.filter_by(service_point_id=service_point_id).count() + 1
        return f"{prefix}{number:03d}"

    @staticmethod
    def join_queue(student_id, service_point_id):
        existing = QueueEntry.query.filter_by(student_id=student_id, service_point_id=service_point_id,
                                               status="WAITING").first()
        if existing:
            return existing
        token = QueueEngine.generate_token(service_point_id)
        entry = QueueEntry(token=token, student_id=student_id, service_point_id=service_point_id)
        db.session.add(entry)
        db.session.add(QueueEvent(service_point_id=service_point_id, token=token, event_type="JOINED"))
        db.session.commit()
        return entry

    @staticmethod
    def get_position(queue_entry_id):
        entry = QueueEntry.query.get(queue_entry_id)
        if not entry:
            return None
        if entry.status != "WAITING":
            return 0
        queue = QueueEngine.get_queue(entry.service_point_id)
        for position, item in enumerate(queue, start=1):
            if item.id == entry.id:
                return position
        return None

    @staticmethod
    def serve_next(service_point_id, counter_id):
        counter = Counter.query.get(counter_id)
        if not counter or counter.service_point_id != service_point_id:
            return None, "INVALID_COUNTER"
        if counter.status == "BUSY":
            return None, "COUNTER_BUSY"
        if counter.status != "OPEN":
            return None, "COUNTER_NOT_OPEN"
        entry = QueueEngine.get_queue(service_point_id)
        if not entry:
            return None, "QUEUE_EMPTY"
        selected = entry[0]
        now = datetime.utcnow()
        selected.status = "SERVING"
        selected.called_at = now
        counter.current_token = selected.token
        counter.status = "BUSY"
        db.session.add(ServiceRecord(queue_entry_id=selected.id, counter_id=counter.id,
                                     service_start=now))
        db.session.add(QueueEvent(service_point_id=service_point_id, token=selected.token,
                                  event_type="CALLED"))
        db.session.commit()
        return selected, "OK"

    @staticmethod
    def complete_service(queue_entry_id):
        entry = QueueEntry.query.get(queue_entry_id)
        if not entry or entry.status != "SERVING":
            return None
        now = datetime.utcnow()
        entry.status = "COMPLETED"
        entry.completed_at = now
        if entry.called_at:
            entry.actual_wait = (entry.called_at - entry.joined_at).total_seconds() / 60
        record = ServiceRecord.query.filter_by(queue_entry_id=entry.id).order_by(ServiceRecord.id.desc()).first()
        if record:
            record.service_end = now
            record.service_duration = max(0, (now - record.service_start).total_seconds() / 60) if record.service_start else None
            counter = Counter.query.get(record.counter_id)
        else:
            counter = Counter.query.filter_by(current_token=entry.token).first()
        if counter:
            counter.current_token = None
            counter.status = "OPEN"
        db.session.add(QueueEvent(service_point_id=entry.service_point_id, token=entry.token,
                                  event_type="COMPLETED"))
        db.session.commit()
        return entry
