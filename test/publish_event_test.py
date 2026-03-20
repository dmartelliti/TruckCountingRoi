import time
import uuid
import io
import asyncio
from datetime import datetime, timezone
from infrastructure.buckets.s3.s3_manager import S3Manager
from infrastructure.brokers.iot.publisher_async import MQTTPublisher
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

import cv2
import matplotlib.pyplot as plt
import numpy as np
from config.settings import settings


ITERATIONS = 100


s3_manager = S3Manager(
    settings.AWS_S3_ACCESS_KEY_ID,
    settings.AWS_S3_SECRET_ACCESS_KEY,
    settings.AWS_S3_BUCKET
)


mqtt_publisher = MQTTPublisher(
    endpoint="a2wzdtjvc9vmtu-ats.iot.us-east-1.amazonaws.com",
    cert=str(BASE_DIR / "infrastructure/brokers/iot/Daniel-device.certs.pem"),
    key=str(BASE_DIR / "infrastructure/brokers/iot/Daniel-device.private.key"),
    ca=str(BASE_DIR / "infrastructure/brokers/iot/AmazonRootCA1.pem"),
    client_id="vcap-new-01"
)

mqtt_topic = "vcap-new-01/Daniel-device/vehiculos"


async def run_benchmark(event):

    s3_times = []
    mqtt_times = []
    total_times = []

    for i in range(ITERATIONS):

        total_start = time.perf_counter()

        now_iso = datetime.now(timezone.utc).isoformat()

        mqtt_payload = {
            "eventId": str(uuid.uuid4()),
            "timestamp": now_iso,
            "source": {
                "clientId": "vcap-new-01",
                "topic": "vcap-new-01/Daniel-device/vehiculos"
            },
            "targetId": "mod-vehicles",
            "priority": 5,
            "type": "vehicle.detection",
            "version": "1.0.0",
            "payload": {
                "roiId": getattr(event.roi, "roi_id", "007"),
                "roiName": getattr(event.roi, "roi_name", "test002"),
                "detection": {
                    "plateNumber": "xxx",
                    "vehicleType": getattr(event.detections[-1], "label", "xxx").upper() if event.detections else "xxx",
                    "direction": event.status.value,
                    "cargo": {
                        "detected": False
                    }
                },
                "evidence": {
                    "frameUrl": ""
                },
                "location": {
                    "latitude": -30.0,
                    "longitude": -33.0
                },
                "detectionTimestamp": getattr(event, "timestamp", now_iso)
            }
        }

        ret, jpeg = cv2.imencode(".jpg", event.frame)

        if ret:

            frame_bytes = io.BytesIO(jpeg.tobytes())
            s3_key = f"events/{event.camera_id}/{event.id}_{int(time.time()*1000)}_2.jpg"

            # -------- S3 timing --------
            s3_start = time.perf_counter()

            await asyncio.to_thread(
                s3_manager.upload_fileobj,
                frame_bytes,
                s3_key
            )

            s3_end = time.perf_counter()
            s3_times.append(s3_end - s3_start)

            public_url = s3_manager.get_public_url(s3_key)

            mqtt_payload["payload"]["evidence"]["frameUrl"] = public_url

        # -------- MQTT timing --------
        mqtt_start = time.perf_counter()

        await mqtt_publisher.publish(
            mqtt_topic,
            mqtt_payload
        )

        mqtt_end = time.perf_counter()
        mqtt_times.append(mqtt_end - mqtt_start)

        total_end = time.perf_counter()
        total_times.append(total_end - total_start)

        print(f"Iteration {i+1}/{ITERATIONS} done")

    return s3_times, mqtt_times, total_times


def plot_histograms(s3_times, mqtt_times, total_times):

    plt.figure()
    plt.hist(s3_times, bins=20)
    plt.title("S3 Upload Time")
    plt.xlabel("Seconds")
    plt.ylabel("Frequency")
    plt.show()

    plt.figure()
    plt.hist(mqtt_times, bins=20)
    plt.title("MQTT Publish Time")
    plt.xlabel("Seconds")
    plt.ylabel("Frequency")
    plt.show()

    plt.figure()
    plt.hist(total_times, bins=20)
    plt.title("Total Processing Time")
    plt.xlabel("Seconds")
    plt.ylabel("Frequency")
    plt.show()


async def main():
    import cv2
    from core.dtos.event_dto import EventDto
    from core.dtos.roi_dto import RoiDTO
    from core.constants import FlowDirectionCode

    from core.dtos.detection_dto import DetectionDto
    from core.dtos.bbox_dto import BBoxDto
    await mqtt_publisher.connect()
    image_path = "/Users/danielmartelliti/Downloads/98_1773403854535.jpg"

    frame = cv2.imread(image_path)

    event = EventDto(
        id=99,
        event_frame=7236,
        status=FlowDirectionCode.ENTRY,
        camera_id="001",
        pipeline_name="truck_counter",
        roi=RoiDTO(
            roi_id="roi_1",
            roi_name="entry_lane",
            polygon=[
                (100, 200),
                (400, 200),
                (400, 500),
                (100, 500)
            ],
            reference_line=((100, 350), (400, 350))
        ),
        frame=frame,
        detections=[
            DetectionDto(
                bbox=BBoxDto(
                    x1=262.0935974121094,
                    y1=363.60205078125,
                    x2=448.0370178222656,
                    y2=477.5816650390625,
                    img_shape=(720, 1280)
                ),
                class_id=2,
                label="car",
                confidence=0.7038953304290771,
                track_id=3918,
                frame_id=7227,
                model_version="models/yolov8n.pt"
            )
        ]
    )

    s3_times, mqtt_times, total_times = await run_benchmark(
        event
    )

    print("\nResults:")
    print("S3 avg:", np.mean(s3_times))
    print("MQTT avg:", np.mean(mqtt_times))
    print("Total avg:", np.mean(total_times))

    plot_histograms(s3_times, mqtt_times, total_times)
    await mqtt_publisher.disconnect()

asyncio.run(main())

