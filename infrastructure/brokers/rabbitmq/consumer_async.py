import asyncio
import json
import aio_pika
from .config import RabbitMQConfig


class RabbitMQConsumer:
    def __init__(self, config: RabbitMQConfig):
        self.config = config
        self._connection = None
        self._channel = None
        self._queue = None

    async def _connect(self):
        self._connection = await aio_pika.connect_robust(
            host=self.config.host,
            port=self.config.port,
            login=self.config.username,
            password=self.config.password,
        )

        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=1)

        self._queue = await self._channel.declare_queue(
            self.config.queue_name,
            durable=True
        )

    async def start_consuming(self, callback):
        """
        callback: async function that receives the deserialized message
        """

        await self._connect()

        async with self._queue.iterator() as queue_iter:
            print("Waiting for messages...")
            async for message in queue_iter:
                async with message.process():
                    body = json.loads(message.body)
                    await callback(body)

    async def close(self):
        if self._connection:
            await self._connection.close()


# Script execution
async def main():
    config = RabbitMQConfig(port=5673)

    async def handle_message(message):
        print(message)

    consumer = RabbitMQConsumer(config)

    try:
        await consumer.start_consuming(handle_message)
    except KeyboardInterrupt:
        await consumer.close()


if __name__ == "__main__":
    asyncio.run(main())