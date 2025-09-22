# run_dashboard.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq_dashboard import DashboardApp
from waitress import serve  # pip install waitress

# ВАЖНО: те же host/port/db/namespace, что у воркеров Dramatiq!
broker = RedisBroker(host="127.0.0.1", port=6379, db=0)  # namespace можно указать явно
# Если используешь кастомные очереди, их нужно объявить:
broker.declare_queue("default")

dramatiq.set_broker(broker)

# Префикс "" даёт корень на /
app = DashboardApp(broker=broker, prefix="")

if __name__ == "__main__":
    serve(app, host="127.0.0.1", port=9199)
