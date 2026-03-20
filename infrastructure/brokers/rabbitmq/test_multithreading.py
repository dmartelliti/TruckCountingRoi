import threading

from infrastructure.brokers.rabbitmq.publisher import RabbitMQPublisher
from infrastructure.brokers.rabbitmq.consumer import RabbitMQConsumer
from infrastructure.brokers.rabbitmq.config import RabbitMQConfig


def run_consumer(config):
    """
    Este código corre dentro del proceso hijo.
    """

    def handle_message(message):
        print(message)

    consumer = RabbitMQConsumer(config)

    consumer.start_consuming(handle_message)


def run_publisher(config):
    """
    Este código corre dentro del proceso hijo.
    """
    event = {
        "eventId": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2026-02-25T14:32:10Z",
        "source": {
            "clientId": "traffic-system-prod",
            "topic": "city/berlin/intersection-12/camera-3",
            "deviceId": "camera-3"
        },
        "targetId": "mod-vehicles",
        "priority": 7,
        "type": "vehicle-detection",
        "version": "1.0.0",
        "metadata": {
            "correlationId": "123e4567-e89b-12d3-a456-426614174000",
            "ttl": 60,
            "tags": ["computer-vision", "edge", "realtime"]
        },
        "payload": {
            "vehicleId": "veh-982341",
            "confidence": 0.94,
            "boundingBox": {
                "x": 412,
                "y": 215,
                "width": 120,
                "height": 65
            },
            "vehicleType": "car",
            "color": "white",
            "speedKmh": 43.7,
            "direction": "north"
        }
    }
    publisher = RabbitMQPublisher(config)
    for _ in range(10):
        publisher.publish(event)




if __name__ == "__main__":
    rabbitmq_config = RabbitMQConfig(port=5673)

    consumer_thread = threading.Thread(
        target=run_consumer,
        args=(rabbitmq_config,)
    )

    publisher_thread = threading.Thread(
        target=run_publisher,
        args=(rabbitmq_config,)
    )

    consumer_thread.start()
    publisher_thread.start()

    consumer_thread.join()
    publisher_thread.join()
