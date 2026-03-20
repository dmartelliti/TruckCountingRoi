import json
import pika
from .config import RabbitMQConfig


class RabbitMQPublisher:
    def __init__(self, config: RabbitMQConfig):
        self.config = config
        self._connection = None
        self._channel = None
        self._connect()

    def _connect(self):
        # Create credentials for authentication
        credentials = pika.PlainCredentials(
            self.config.username,
            self.config.password
        )

        # Configure connection parameters
        parameters = pika.ConnectionParameters(
            host=self.config.host,
            port=self.config.port,
            credentials=credentials
        )

        # Establish connection and channel
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()

        # Declare the queue (idempotent operation)
        self._channel.queue_declare(queue=self.config.queue_name, durable=True)

    def publish(self, message: dict):
        # Serialize message to JSON
        body = json.dumps(message)

        # Publish message to the queue
        self._channel.basic_publish(
            exchange="",
            routing_key=self.config.queue_name,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2  # Make message persistent
            ),
        )

    def close(self):
        # Close connection safely
        if self._connection and not self._connection.is_closed:
            self._connection.close()