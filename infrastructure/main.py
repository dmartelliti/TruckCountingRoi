import io
import time
import logging
import asyncio
import cv2
import threading
import numpy as np

from flask import Flask, Response

from core.dtos.roi_dto import RoiDTO
from infrastructure.commands.base_command import BaseCommand
from infrastructure.brokers.rabbitmq.config import RabbitMQConfig
from infrastructure.brokers.rabbitmq.consumer_async import RabbitMQConsumer
from multiprocessing import Queue, Process
from application.application_manager import ApplicationManager
from infrastructure.brokers.iot.publisher_async import MQTTPublisher
from infrastructure.buckets.s3.s3_manager import S3Manager
from application.dtos.frame_stream_dto import FrameStreamDto
from config.settings import settings

from datetime import datetime, timezone
import uuid

from collections import Counter
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------
# Logging configuration (global)
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("Main")

s3_manager = S3Manager(
    settings.AWS_S3_ACCESS_KEY_ID,
    settings.AWS_S3_SECRET_ACCESS_KEY,
    settings.AWS_S3_BUCKET
)

mqtt_publisher = MQTTPublisher(
    endpoint=settings.MQTT_ENDPOINT,
    cert=settings.MQTT_CERT,
    key=settings.MQTT_KEY,
    ca=settings.MQTT_CA,
    client_id=settings.MQTT_CLIENT_ID
)

mqtt_topic = settings.MQTT_TOPIC


# ------------------------------------------------------------------
# Process + Queues
# ------------------------------------------------------------------
application_manager = ApplicationManager(None)

instruction_queue = Queue()
event_queue = Queue()
frame_queue = Queue()

application_process = Process(
    target=application_manager.run,
    args=(event_queue, instruction_queue, frame_queue)
)


# ------------------------------------------------------------------
# Streaming server
# ------------------------------------------------------------------
app = Flask(__name__)

latest_frames = {}
frame_lock = threading.Lock()

event_counter = {}


# ------------------------------------------------------------------
# Video Stream
# ------------------------------------------------------------------
def generate_stream(camera_id):

    while True:
        time.sleep(0.1)

        with frame_lock:

            frame = latest_frames.get(camera_id)

            if frame is None:
                continue

            ret, jpeg = cv2.imencode(".jpg", frame)

            if not ret:
                continue

            frame_bytes = jpeg.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes +
            b"\r\n"
        )


@app.route("/stream/<camera_id>")
def stream(camera_id):

    return Response(
        generate_stream(camera_id),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ------------------------------------------------------------------
# Stats Stream
# ------------------------------------------------------------------
def generate_stats_stream(camera_id):

    while True:
        time.sleep(0.5)

        counter = event_counter.get(camera_id, Counter())

        enter_count = counter.get("ENTRY", 0)
        exit_count = counter.get("EXIT", 0)

        labels = ["ENTRY", "EXIT"]
        values = [enter_count, exit_count]

        fig, ax = plt.subplots()

        ax.bar(labels, values)
        ax.set_title(f"Vehicle Flow - Camera {camera_id}")
        ax.set_xlabel("Direction")
        ax.set_ylabel("Count")
        ax.grid(axis="y")

        fig.canvas.draw()

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)

        img = np.frombuffer(buf.getvalue(), dtype=np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)

        plt.close(fig)

        ret, jpeg = cv2.imencode(".jpg", img)
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + jpeg.tobytes() +
            b"\r\n"
        )




@app.route("/stats/<camera_id>")
def stats(camera_id):

    return Response(
        generate_stats_stream(camera_id),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/cameras")
def cameras():

    with frame_lock:
        return {"cameras": list(latest_frames.keys())}


def start_stream_server():
    logger.info("Starting streaming server on port 8080")
    app.run(host="0.0.0.0", port=8080, threaded=True, use_reloader=False)


# ------------------------------------------------------------------
# Rabbit Consumer
# ------------------------------------------------------------------
async def run_consumer(config: RabbitMQConfig):

    consumer_logger = logging.getLogger("RabbitConsumer")

    async def handle_message(raw_json_string):
        try:
            consumer_logger.info("Message received from RabbitMQ")
            consumer_logger.info(f"{raw_json_string}")

            input_dto = BaseCommand.model_validate(raw_json_string)

            instruction_queue.put(input_dto)

        except Exception as e:
            consumer_logger.exception(f"Error handling message: {e}")

    consumer = RabbitMQConsumer(config)
    await consumer.start_consuming(handle_message)


# ------------------------------------------------------------------
# Event Queue Consumer
# ------------------------------------------------------------------
async def consume_event_queue():

    global event_counter

    queue_logger = logging.getLogger("EventQueueConsumer")

    while True:
        try:
            event = await asyncio.to_thread(event_queue.get)

            await publish_event(event, queue_logger)

        except Exception as e:
            queue_logger.exception(f"Error consuming event_queue: {e}")

        await asyncio.sleep(0.1)


async def publish_event(event, queue_logger):
        camera_id = event.camera_id

        if camera_id not in event_counter:
            event_counter[camera_id] = Counter()

        event_counter[camera_id][event.status.value] += 1

        queue_logger.info(f"Consumed from event_queue: {event.to_dict_without_frame()}")

        # -----------------------------------
        # MQTT publish
        # -----------------------------------
        try:
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
                        "xyxy": event.detections[-1].bbox.xyxy,
                        "xywh": event.detections[-1].bbox.xywh,
                        "confidence": event.detections[-1].confidence,
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

                s3_key = f"events/{event.camera_id}/{event.id}_{int(time.time() * 1000)}.jpg"

                await asyncio.to_thread(
                    s3_manager.upload_fileobj,
                    frame_bytes,
                    s3_key
                )

                presigned_url = s3_manager.generate_presigned_url(s3_key)

                mqtt_payload["payload"]["evidence"]["frameUrl"] = presigned_url

                print(mqtt_payload)

            start = time.perf_counter()

            await mqtt_publisher.publish(
                mqtt_topic,
                mqtt_payload
            )

            end = time.perf_counter()

            print(f"Publish took {end - start:.6f} seconds")

        except Exception as mqtt_error:
            queue_logger.exception(f"MQTT publish failed: {mqtt_error}")

# ------------------------------------------------------------------
# Frame Queue Consumer
# ------------------------------------------------------------------
async def consume_frame_queue():

    frame_logger = logging.getLogger("FrameQueueConsumer")

    while True:
        try:
            frame_dto: FrameStreamDto = await asyncio.to_thread(frame_queue.get)

            frame = frame_dto.frame
            rois = frame_dto.rois
            camera_id = frame_dto.camera_id
            rois = [rois] if isinstance(rois, RoiDTO) else rois

            for roi in rois:
                if roi is not None and roi.polygon:
                    points = np.array(roi.polygon, dtype=np.int32)

                    cv2.polylines(
                        frame,
                        [points],
                        isClosed=True,
                        color=(255, 0, 0),
                        thickness=2
                    )

                    label_pos = tuple(points[0])

                    cv2.putText(
                        frame,
                        f"ROI: {roi.roi_id}",
                        label_pos,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 0, 0),
                        2,
                        cv2.LINE_AA
                    )

                    if roi.reference_line is not None:
                        p1, p2 = roi.reference_line
                        cv2.line(
                            frame,
                            tuple(map(int, p1)),
                            tuple(map(int, p2)),
                            (0, 255, 0),
                            2
                        )

            with frame_lock:
                latest_frames[camera_id] = frame

        except Exception as e:
            frame_logger.exception(f"Error consuming frame_queue: {e}")

        await asyncio.sleep(0.01)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
async def main():

    config = RabbitMQConfig(port=5673)

    await mqtt_publisher.connect()

    consumer_task = asyncio.create_task(run_consumer(config))
    event_queue_task = asyncio.create_task(consume_event_queue())
    frame_queue_task = asyncio.create_task(consume_frame_queue())

    await asyncio.gather(
        consumer_task,
        event_queue_task,
        frame_queue_task
    )


# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------
async def main2():
    await mqtt_publisher.connect()

    event = {'eventId': '213101b4-32df-412a-937a-fb589d57323c', 'timestamp': '2026-03-10T16:03:20.277438+00:00',
             'source': {'clientId': 'vcap-new-01', 'topic': 'vcap-new-01/Daniel-device/vehiculos'},
             'targetId': 'mod-vehicles', 'priority': 5, 'type': 'vehicle.detection', 'version': '1.0.0',
             'payload': {'roiId': 'roi_1', 'roiName': 'entry_lane',
                         'detection': {'plateNumber': 'xxx', 'vehicleType': 'car', 'direction': 'ENTER',
                                       'cargo': {'detected': False}}, 'evidence': {
                     'frameUrl': 'https://electro-test-bucket-2026.s3.amazonaws.com/events/001/4_1773158600294.jpg'},
                         'location': {'latitude': -30.0, 'longitude': -33.0},
                         'detectionTimestamp': '2026-03-10T16:03:20.277438+00:00'}}

    await mqtt_publisher.publish(mqtt_topic, event)

    await mqtt_publisher.disconnect()

if __name__ == "__main__":
    application_process.start()

    threading.Thread(
        target=start_stream_server,
        daemon=True
    ).start()

    try:
        asyncio.run(main())
    finally:
        application_process.terminate()
        application_process.join()

    # asyncio.run(main2())