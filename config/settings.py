import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    # MQTT
    MQTT_ENDPOINT = os.getenv("MQTT_ENDPOINT")
    MQTT_CERT = str(BASE_DIR / Path(os.getenv("MQTT_CERT", "")))
    MQTT_KEY = str(BASE_DIR / Path(os.getenv("MQTT_KEY", "")))
    MQTT_CA = str(BASE_DIR / Path(os.getenv("MQTT_CA", "")))
    MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
    MQTT_TOPIC = os.getenv("MQTT_TOPIC")

    # AWS S3
    AWS_S3_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY_ID")
    AWS_S3_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

    # RabbitMQ
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
    RABBITMQ_AMQP_PORT = int(os.getenv("RABBITMQ_AMQP_PORT", 5672))
    RABBITMQ_MANAGEMENT_PORT = int(os.getenv("RABBITMQ_MANAGEMENT_PORT", 15672))
    RABBITMQ_USER = os.getenv("RABBITMQ_USER")
    RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")


settings = Settings()
