import json
from infrastructure.brokers.rabbitmq.publisher import RabbitMQPublisher
from infrastructure.brokers.rabbitmq.config import RabbitMQConfig


def run_publisher(command, config):

    publisher = RabbitMQPublisher(config)
    publisher.publish(command)

if __name__ == "__main__":
    rabbitmq_config = RabbitMQConfig(port=5673)

    with open("update_roi.json", "r", encoding="utf-8") as f:
        _command = json.load(f)

    run_publisher(_command, rabbitmq_config)