import asyncio
import json
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
from .config import IoTConfig


class IoTConsumer:

    def __init__(self, config: IoTConfig):
        print(config)

        self.config = config
        self._connection = None
        self._callback = None

    async def connect(self):

        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

        self._connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.config.endpoint,
            cert_filepath=self.config.cert_file,
            pri_key_filepath=self.config.key_file,
            ca_filepath=self.config.root_ca,
            client_bootstrap=client_bootstrap,
            client_id=self.config.client_id + "-consumer",
            clean_session=False,
            keep_alive_secs=30
        )

        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._connection.connect().result()
        )

    def _on_message(self, topic, payload, **kwargs):

        message = json.loads(payload.decode())

        asyncio.create_task(self._callback(message))

    async def start_consuming(self, callback):

        self._callback = callback

        await self.connect()

        for topic in self.config.topics:

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._connection.subscribe(
                    topic=topic,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self._on_message
                )[0].result()
            )

        print("Waiting for messages...")

        while True:
            await asyncio.sleep(1)

    async def close(self):

        if self._connection:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._connection.disconnect().result()
            )


# Script execution
async def main():

    config = IoTConfig.from_json("config/iot_config.json")

    async def handle_message(message):
        print("Received message:")
        print(message)

    consumer = IoTConsumer(config)

    try:
        await consumer.start_consuming(handle_message)
    except KeyboardInterrupt:
        await consumer.close()


if __name__ == "__main__":
    asyncio.run(main())