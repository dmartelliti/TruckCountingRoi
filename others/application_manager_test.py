import threading
import logging

from application.application_manager import ApplicationManager
from application.dtos.command_dto import CommandDTO
from uuid import UUID
from datetime import datetime
from infrastructure.dtos.source_dto import Source

from multiprocessing import Queue, Process


# ------------------------------------------------------------------
# Logging configuration
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(processName)s | %(threadName)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Process + Queues
# ------------------------------------------------------------------
application_manager = ApplicationManager(None)

instruction_queue = Queue()
event_queue = Queue()

application_process = Process(
    target=application_manager.run,
    args=(event_queue, instruction_queue),
    name="ApplicationProcess"
)


def run_receiver():
    logger.info("Receiver thread started")

    while True:
        logger.info("Waiting for event...")
        resolve = event_queue.get()
        logger.info(f"Event received: {resolve}")


def run_sender():
    logger.info("Sender thread started")

    command = CommandDTO(
        eventId=UUID(int=0),
        timestamp=datetime.now(),
        source=Source(clientId='test', topic='test'),
        targetId='test',
        priority=1,
        type='test',
        version='test',
        payload={},
        metadata=None
    )

    for i in range(10):
        logger.info(f"Sending command {i+1}")
        instruction_queue.put(command)

    logger.info("Sender finished sending commands")


if __name__ == "__main__":

    logger.info("Starting application process")
    application_process.start()

    receiver_thread = threading.Thread(
        target=run_receiver,
        name="ReceiverThread",
        daemon=True
    )

    sender_thread = threading.Thread(
        target=run_sender,
        name="SenderThread"
    )

    logger.info("Starting threads")

    receiver_thread.start()
    sender_thread.start()

    sender_thread.join()

    logger.info("Sender thread finished")

    application_process.terminate()
    application_process.join()

    logger.info("Application process terminated")