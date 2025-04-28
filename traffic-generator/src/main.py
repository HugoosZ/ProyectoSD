from distributions import uniform_distribution, exponential_distribution
import time
import sys

sys.path.insert(0, "/storage/src")
sys.path.insert(0, "/cache-service/src")


from mongo_storage import MongoStorage
from cache_manager import RedisCache

mongo_storage = MongoStorage()
cache_service = RedisCache()


class TrafficGenerator:
    def simulate_traffic(self, distribution_type: str, rate: float, duration: int):
        if distribution_type == "uniform":
            intervals = uniform_distribution(rate, duration)
        elif distribution_type == "exponential":
            intervals = exponential_distribution(rate, duration)
        else:
            raise ValueError("Distribución no soportada")

        for i, interval in enumerate(intervals):
            time.sleep(interval)  # Espera el tiempo generado
            self.execute_query()  # Tu lógica de consulta a Redis/MongoDB
            print(f"Consulta {i} | Distribución: {distribution_type} | Intervalo: {interval:.2f}s")