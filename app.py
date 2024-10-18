import os
import logging
import asyncio
import signal
from queue import Queue
from threading import Thread
import redis

# Import FTP server components
from ftp_server.main import start_ftp_server

# Import image processing components
from image_processing.main import ImageProcessor
from image_processing.telegram_bot import TelegramBot
from image_processing.signl4_alerting import SIGNL4Alerter

# Import configuration
from config import (
    USERS, FTP_HOST, FTP_PORT, MAIN_FTP_DIRECTORY, MAX_IMAGE_QUEUE,
    POSITIVE_PHOTOS_DIRECTORY, TELEGRAM_BOT_TOKEN, REDIS_HOST,
    REDIS_PORT, REDIS_PASSWORD, REDIS_ARMED_KEY_PREFIX
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

def create_user_directories():
    for user_id, user_data in USERS.items():
        user_directory = os.path.join(MAIN_FTP_DIRECTORY, user_id)
        os.makedirs(user_directory, exist_ok=True)
        logger.info(f"Created or verified directory for user {user_data['FTP_USER']}: {user_directory}")

async def process_image_queue(image_queue, image_processor):
    while True:
        try:
            if not image_queue.empty():
                image_path, user_settings = image_queue.get()
                await image_processor.process_image(image_path, user_settings, delete_after_processing=True)
            else:
                await asyncio.sleep(1)  # Sleep for a short time if the queue is empty
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")

async def auto_arm_checker(image_processor):
    while True:
        for user, user_settings in USERS.items():
            image_processor.check_and_auto_arm(user, user_settings)
        await asyncio.sleep(60)  # Check every minute

def initialize_armed_status():
    for user, user_settings in USERS.items():
        if redis_client.get(f"{REDIS_ARMED_KEY_PREFIX}{user}") is None:
            redis_client.set(f"{REDIS_ARMED_KEY_PREFIX}{user}", str(user_settings['ARMED']).lower())
            logger.info(f"Initialized armed status for user {user} in Redis")

async def main():
    # Create necessary directories
    os.makedirs(MAIN_FTP_DIRECTORY, exist_ok=True)
    os.makedirs(POSITIVE_PHOTOS_DIRECTORY, exist_ok=True)
    create_user_directories()

    # Initialize armed status in Redis
    initialize_armed_status()

    # Create shared queue for image processing
    image_queue = Queue(maxsize=MAX_IMAGE_QUEUE)

    # Initialize components
    telegram_bot = TelegramBot(TELEGRAM_BOT_TOKEN)
    signl4_alerter = SIGNL4Alerter(redis_client)
    image_processor = ImageProcessor(telegram_bot, signl4_alerter, redis_client)

    # Start FTP server
    ftp_server = start_ftp_server(FTP_HOST, FTP_PORT, image_queue)

    # Start background tasks
    image_processing_task = asyncio.create_task(process_image_queue(image_queue, image_processor))
    auto_arm_task = asyncio.create_task(auto_arm_checker(image_processor))

    # Set up graceful shutdown
    loop = asyncio.get_running_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop, ftp_server, image_processing_task, auto_arm_task))
        )

    logger.info("Application started successfully")

    # Keep the main coroutine running
    while True:
        await asyncio.sleep(3600)  # Sleep for an hour, or use another condition to keep the loop running

async def shutdown(signal, loop, ftp_server, *tasks):
    logger.info(f"Received exit signal {signal.name}...")
    logger.info("Closing FTP server...")
    ftp_server.close()

    logger.info("Cancelling background tasks...")
    for task in tasks:
        task.cancel()

    logger.info("Shutting down asyncio tasks...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    logger.info("Stopping event loop...")
    loop.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Exiting...")
    finally:
        logger.info("Application shutdown complete.")