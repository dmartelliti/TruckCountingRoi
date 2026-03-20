import json
import asyncio

from awsiot import mqtt_connection_builder
from awscrt import mqtt


class MQTTPublisher:

    def __init__(
        self,
        endpoint: str,
        cert_path: str,
        key_path: str,
        ca_path: str,
        client_id: str,
    ):

        self.endpoint = endpoint
        self.client_id = client_id

        self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=endpoint,
            cert_filepath=cert_path,
            pri_key_filepath=key_path,
            ca_filepath=ca_path,
            client_id=client_id,
            clean_session=False,
            keep_alive_secs=30,
        )

    async def connect(self):
        print("Connecting...")

        future = self.mqtt_connection.connect()
        await asyncio.wrap_future(future)

        print("Connected!")

    async def publish(self, topic: str, payload: dict, qos=mqtt.QoS.AT_LEAST_ONCE):
        message = json.dumps(payload)

        future, packet_id = self.mqtt_connection.publish(
            topic=topic,
            payload=message,
            qos=qos
        )

        await asyncio.wrap_future(future)

        print(f"Published to {topic} (packet_id={packet_id})")

    async def disconnect(self):
        future = self.mqtt_connection.disconnect()
        await asyncio.wrap_future(future)

        print("Disconnected!")

async def main():

    endpoint = "a2wzdtjvc9vmtu-ats.iot.us-east-1.amazonaws.com"

    publisher = MQTTPublisher(
        endpoint=endpoint,
        cert_path="Daniel-device.certs.pem",
        key_path="Daniel-device.private.key",
        ca_path="AmazonRootCA1.pem",
        client_id="vcap-new-01"
    )

    await publisher.connect()

    topic = "vcap-new-01/Daniel-device/vehiculos"

    event = {
        "eventId": "5523a9ce-8bda-4de8-a1cc-8b2baa3e0000",
        "timestamp": "2026-03-05T19:06:05.279054+00:00",
        "source": {
            "clientId": "vcap-new-01",
            "topic": topic
        },
        "targetId": "mod-vehicles",
        "priority": 5,
        "type": "test_event",
        "version": "1.0.0",
        "payload": {
            "roiId": "007",
            "roiName": "Roi 1",
            "detection": {
                "plateNumber": "xxx",
                "vehicleType": "CAR",
                "direction": "ENTRY",
                "cargo": {
                    "detected": False
                }
            }
        }
    }

    await publisher.publish(topic, event)

    await publisher.disconnect()


if __name__ == "__main__":
    asyncio.run(main())