import io
import time
import logging
import asyncio
import cv2
import threading
import numpy as np

from flask import Flask, Response

from infrastructure.commands.base_command import BaseCommand
from infrastructure.brokers.rabbitmq.config import RabbitMQConfig
from infrastructure.brokers.rabbitmq.consumer_async import RabbitMQConsumer
from multiprocessing import Queue, Process
from application.application_manager import ApplicationManager

from collections import Counter
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


# ------------------------------------------------------------------
# Logging configuration (global)
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("Main")


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

# event counter
event_counter = {}


# ------------------------------------------------------------------
# Video Stream
# ------------------------------------------------------------------
def generate_stream(camera_id):

    while True:

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

        counter = event_counter.get(camera_id, Counter())

        enter_count = counter.get("ENTER", 0)
        exit_count = counter.get("EXIT", 0)

        labels = ["ENTER", "EXIT"]
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

        time.sleep(0.5)

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

            camera_id = event.camera_id

            if camera_id not in event_counter:
                event_counter[camera_id] = Counter()

            event_counter[camera_id][event.status.value] += 1

            queue_logger.info(f"Consumed from event_queue: {event}")

        except Exception as e:
            queue_logger.exception(f"Error consuming event_queue: {e}")

        await asyncio.sleep(0.1)


# ------------------------------------------------------------------
# Frame Queue Consumer
# ------------------------------------------------------------------
async def consume_frame_queue():
    global latest_frame

    frame_logger = logging.getLogger("FrameQueueConsumer")

    while True:
        try:
            frame_dto = await asyncio.to_thread(frame_queue.get)

            frame = frame_dto.frame
            p1 = frame_dto.line_p1
            p2 = frame_dto.line_p2
            roi = frame_dto.roi
            camera_id = frame_dto.camera_id

            if p1 is not None and p2 is not None:
                cv2.line(
                    frame,
                    tuple(map(int, p1)),
                    tuple(map(int, p2)),
                    (0, 255, 0),
                    2
                )

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