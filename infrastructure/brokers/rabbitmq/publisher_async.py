import asyncio
import json
import aio_pika
from aio_pika import DeliveryMode, Message
from .config import RabbitMQConfig


class RabbitMQPublisher:
    def __init__(self, config: RabbitMQConfig):
        self.config = config
        print(config.host, config.port, config.username, config.password)
        self._connection = None
        self._channel = None

    async def connect(self):
        self._connection = await aio_pika.connect_robust(
            host=self.config.host,
            port=self.config.port,
            login=self.config.username,
            password=self.config.password,
        )

        self._channel = await self._connection.channel()

        await self._channel.declare_queue(
            self.config.queue_name,
            durable=True
        )

    async def publish(self, message: dict):
        body = json.dumps(message).encode()

        await self._channel.default_exchange.publish(
            Message(
                body=body,
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key=self.config.queue_name
        )

    async def close(self):
        if self._connection:
            await self._connection.close()


# Script execution
async def main():
    config = RabbitMQConfig(port=5673)

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

    await publisher._connect()

    for _ in range(10):
        await publisher.publish(event)

    await publisher.close()


if __name__ == "__main__":
    asyncio.run(main())