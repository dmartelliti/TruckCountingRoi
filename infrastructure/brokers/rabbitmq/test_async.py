import asyncio
from infrastructure.brokers.rabbitmq.config import RabbitMQConfig
from infrastructure.brokers.rabbitmq.consumer_async import RabbitMQConsumer
from infrastructure.brokers.rabbitmq.publisher_async import RabbitMQPublisher


async def run_consumer(config: RabbitMQConfig):
    async def handle_message(message):
        print("Received:", message)

    consumer = RabbitMQConsumer(config)
    await consumer.start_consuming(handle_message)


async def run_publisher(config: RabbitMQConfig):
    publisher = RabbitMQPublisher(config)
    await publisher.connect()

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

    # Publica 10 mensajes con pequeña pausa
    for _ in range(10):
        await publisher.publish(event)
        await asyncio.sleep(0.5)

    await publisher.close()


async def main():
    config = RabbitMQConfig(port=5673)

    consumer_task = asyncio.create_task(run_consumer(config))
    publisher_task = asyncio.create_task(run_publisher(config))

    await asyncio.gather(consumer_task, publisher_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")