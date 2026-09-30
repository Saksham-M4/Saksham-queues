from datetime import datetime
from services.queue_engine import QueueEngine
from services.waiting_time import WaitingTimeService


def recommendation(service_point_id):
    queue = QueueEngine.get_queue(service_point_id)
    active = QueueEngine.get_active_counters(service_point_id)
    busy = QueueEngine.get_busy_counters(service_point_id)
    avg = WaitingTimeService.get_average_service_time(service_point_id)
    total = len(queue)
    total_counters = active + busy

    if total_counters == 0:
        return {
            "title": "Counters unavailable",
            "message": "Open a counter before accepting more students.",
            "action": "OPEN_COUNTER",
            "priority": "HIGH",
        }
    if total >= 10 and active < 3:
        return {
            "title": "High queue pressure",
            "message": "Consider opening another counter to reduce estimated waiting time.",
            "action": "OPEN_COUNTER",
            "priority": "HIGH",
        }
    if total >= 5:
        return {
            "title": "Moderate queue pressure",
            "message": "Queue is building. Monitor service speed during the next 15 minutes.",
            "action": "MONITOR",
            "priority": "MEDIUM",
        }
    return {
        "title": "Queue flowing normally",
        "message": f"Average service time is about {avg:.1f} minutes. Current load is manageable.",
        "action": "NORMAL",
        "priority": "LOW",
    }


def peak_window():
    hour = datetime.now().hour
    if hour < 11:
        return "12:00–2:00 PM", "Peak period approaching"
    if hour < 14:
        return "12:00–2:00 PM", "Current peak window"
    if hour < 16:
        return "12:00–2:00 PM", "Peak period has passed"
    return "12:00–2:00 PM", "Next peak window"
