from dataclasses import dataclass


@dataclass
class RabbitMQConfig:
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    queue_name: str = "default_queue"