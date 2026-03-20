import json

if __name__ == '__main__':
    from awsiot import mqtt_connection_builder
    from awscrt import io, mqtt
    import asyncio

    endpoint = "a2wzdtjvc9vmtu-ats.iot.us-east-1.amazonaws.com"

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath="Daniel-device.certs.pem",
        pri_key_filepath="Daniel-device.private.key",
        ca_filepath="AmazonRootCA1.pem",
        client_id="vcap-new-01",
        clean_session=False,
        keep_alive_secs=30,
    )

    print("Connecting...")

    connect_future = mqtt_connection.connect()
    connect_future.result()

    print("Connected!")

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


    topic = "vcap-new-01/Daniel-device/vehiculos"

    payload2 = json.dumps(event)

    payload = """{
  "eventId": "5523a9ce-8bda-4de8-a1cc-8b2baa3e0000", #
  "timestamp": "2026-03-05T19:06:05.279054+00:00", #
  "source": {
    "clientId": "vcap-new-01",
    "topic": "vcap-new-01/Daniel-device/vehiculos"
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
      "vehicleType": "CAR", #
      "direction": "ENTRY", #
      "cargo": {
        "detected": false
      }
    },
    "evidence": {
      "frameUrl": "https://plus.unsplash.com/premium_photo-1664695368767-c42483a0bda1?q=80&w=2672&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    },
    "location": {
      "latitude": -30.0,
      "longitude": -33.0
    },
    "detectionTimestamp": "2026-03-02T14:38:03+00:00"
  }
}"""

    mqtt_connection.publish(
        topic=topic,
        payload=payload,
        qos=mqtt.QoS.AT_LEAST_ONCE
    )
    # asyncio.get_event_loop().run_in_executor(
    #     None,
    #     lambda:
    # )

    mqtt_connection.disconnect().result()
    print("Disconnected!")
