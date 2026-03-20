import json
import pika
from .config import RabbitMQConfig


class RabbitMQConsumer:
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

    def start_consuming(self, callback):
        """
        callback: function that receives the deserialized message
        """

        def _callback(ch, method, properties, body):
            # Deserialize message from JSON
            message = json.loads(body)

            # Execute user-defined callback
            callback(message)

            # Acknowledge message processing
            ch.basic_ack(delivery_tag=method.delivery_tag)

        # Ensure fair dispatch (one message per worker)
        self._channel.basic_qos(prefetch_count=1)

        # Register consumer callback
        self._channel.basic_consume(
            queue=self.config.queue_name,
            on_message_callback=_callback
        )

        print("Waiting for messages...")
        self._channel.start_consuming()

    def close(self):
        # Close connection safely
        if self._connection and not self._connection.is_closed:
            self._connection.close()