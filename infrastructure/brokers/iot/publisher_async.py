from awsiot import mqtt_connection_builder
from awscrt import mqtt
import logging

import asyncio
import json


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("Main")


class MQTTPublisher:

    def __init__(self, endpoint, cert, key, ca, client_id):

        self.connection = mqtt_connection_builder.mtls_from_path(
            endpoint=endpoint,
            cert_filepath=cert,
            pri_key_filepath=key,
            ca_filepath=ca,
            client_id=client_id,
            clean_session=False,
            keep_alive_secs=30,
        )

    async def connect(self):
        future = self.connection.connect()
        await asyncio.wrap_future(future)
        logger.info("MQTT connected")

    async def publish(self, topic, payload):

        message = json.dumps(payload)

        future, _ = self.connection.publish(
            topic=topic,
            payload=message,
            qos=mqtt.QoS.AT_LEAST_ONCE
        )

        await asyncio.wrap_future(future)

    async def disconnect(self):
        future = self.connection.disconnect()
        await asyncio.wrap_future(future)
        logger.info("MQTT disconnected")