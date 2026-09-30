from database.models import ServiceRecord, QueueEntry
from services.queue_engine import QueueEngine

class WaitingTimeService:
    MAX_HISTORY = 20
    FALLBACK_SERVICE_TIME = 3.0

    @staticmethod
    def get_average_service_time(service_point_id):
        records = (ServiceRecord.query.join(QueueEntry, ServiceRecord.queue_entry_id == QueueEntry.id)
                   .filter(QueueEntry.service_point_id == service_point_id,
                           ServiceRecord.service_duration.isnot(None))
                   .order_by(ServiceRecord.id.desc()).limit(WaitingTimeService.MAX_HISTORY).all())
        if not records:
            return WaitingTimeService.FALLBACK_SERVICE_TIME
        return round(sum(r.service_duration for r in records) / len(records), 2)

    @staticmethod
    def get_history_count(service_point_id):
        return ServiceRecord.query.join(QueueEntry, ServiceRecord.queue_entry_id == QueueEntry.id)\
            .filter(QueueEntry.service_point_id == service_point_id,
                    ServiceRecord.service_duration.isnot(None)).count()

    @staticmethod
    def calculate_eta(service_point_id, people_ahead):
        active = QueueEngine.get_active_counters(service_point_id)
        busy = QueueEngine.get_busy_counters(service_point_id)
        available = max(1, active + busy)
        average = WaitingTimeService.get_average_service_time(service_point_id)
        # Approximate queue throughput across all counters.
        eta = (people_ahead * average) / available
        return max(0, round(eta, 1))
