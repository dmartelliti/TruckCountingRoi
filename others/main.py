import json
import logging
import asyncio
from infrastructure.dtos.command_dto import CommandDTO
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

application_process = Process(
    target=application_manager.run,
    args=(event_queue, instruction_queue)
)


# ------------------------------------------------------------------
# Rabbit Consumer
# ------------------------------------------------------------------
async def run_consumer(config: RabbitMQConfig):
    consumer_logger = logging.getLogger("RabbitConsumer")

    async def handle_message(raw_json_string):
        try:
            consumer_logger.info("Message received from RabbitMQ")

            input_dto = CommandDTO.model_validate(raw_json_string)

            instruction_queue.put(input_dto)

            consumer_logger.info(
                f"Event pushed to event_queue | eventId={input_dto.eventId}"
            )

        except Exception as e:
            consumer_logger.exception(f"Error handling message: {e}")

    # consumer_logger.info("Starting RabbitMQ consumer...")
    consumer = RabbitMQConsumer(config)
    await consumer.start_consuming(handle_message)


# ------------------------------------------------------------------
# Rabbit Publisher
# ------------------------------------------------------------------
async def run_publisher(config: RabbitMQConfig):
    publisher_logger = logging.getLogger("RabbitPublisher")

    # publisher_logger.info("Connecting RabbitMQ publisher...")
    publisher = RabbitMQPublisher(config)
    await publisher.connect()
    # publisher_logger.info("Publisher connected")

    with open("../infrastructure/event.json", "r", encoding="utf-8") as f:
        event_data = json.load(f)

    # publisher_logger.info("Publishing test events...")

    for i in range(2):
        await publisher.publish(event_data)
        # publisher_logger.info(f"Published event {i + 1}/10")
        await asyncio.sleep(0.5)

    await publisher.close()
    publisher_logger.info("Publisher connection closed")


# ------------------------------------------------------------------
# Event Queue Consumer (non-blocking)
# ------------------------------------------------------------------
async def consume_event_queue():
    queue_logger = logging.getLogger("EventQueueConsumer")

    # queue_logger.info("Event queue consumer started")

    while True:
        try:
            event = await asyncio.to_thread(event_queue.get)

            queue_logger.info(f"Consumed from event_queue: {event}")

        except Exception as e:
            queue_logger.exception(f"Error consuming event_queue: {e}")

        await asyncio.sleep(0.1)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
async def main():
    # logger.info("Application starting...")
    config = RabbitMQConfig(port=5673)

    consumer_task = asyncio.create_task(run_consumer(config))
    publisher_task = asyncio.create_task(run_publisher(config))
    event_queue_task = asyncio.create_task(consume_event_queue())

    await asyncio.gather(
        consumer_task,
        publisher_task,
        event_queue_task
    )


if __name__ == "__main__":
    # logger.info("Starting ApplicationManager process...")
    application_process.start()
    # logger.info(f"ApplicationManager PID: {application_process.pid}")

    try:
        asyncio.run(main())
    finally:
        # logger.info("Shutting down application process...")
        application_process.terminate()
        application_process.join()
        # logger.info("Application terminated cleanly")