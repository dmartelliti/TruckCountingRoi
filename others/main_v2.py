import json
import logging
import asyncio
import cv2
import threading

from flask import Flask, Response

from infrastructure.commands.base_command import BaseCommand
from infrastructure.brokers.rabbitmq.config import RabbitMQConfig
from infrastructure.brokers.rabbitmq.consumer_async import RabbitMQConsumer
from infrastructure.brokers.rabbitmq.publisher_async import RabbitMQPublisher
from multiprocessing import Queue, Process
from application.application_manager import ApplicationManager


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

latest_frame = None
frame_lock = threading.Lock()


def generate_stream():
    global latest_frame

    while True:
        with frame_lock:
            if latest_frame is None:
                continue

            ret, jpeg = cv2.imencode(".jpg", latest_frame)
            if not ret:
                continue

            frame_bytes = jpeg.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame_bytes +
            b"\r\n"
        )


@app.route("/stream")
def stream():
    return Response(
        generate_stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


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
    queue_logger = logging.getLogger("EventQueueConsumer")

    while True:
        try:
            event = await asyncio.to_thread(event_queue.get)

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
            frame = await asyncio.to_thread(frame_queue.get)
            with frame_lock:
                latest_frame = frame

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