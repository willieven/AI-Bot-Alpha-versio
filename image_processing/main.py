from object_detection import ObjectDetector
from image_manipulation import add_watermark, draw_detections
from telegram_bot import TelegramBot
from signl4_alerting import SIGNL4Alerter
from utils import is_within_working_hours, cleanup_files, save_positive_photo
import logging
import redis
from config import YOLO_MODEL, TELEGRAM_BOT_TOKEN, POSITIVE_PHOTOS_DIRECTORY, SAVE_POSITIVE_PHOTOS, MAIN_FTP_DIRECTORY, USERS, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

class ImageProcessor:
    def __init__(self):
        self.object_detector = ObjectDetector(YOLO_MODEL)
        self.telegram_bot = TelegramBot(TELEGRAM_BOT_TOKEN)
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        self.signl4_alerter = SIGNL4Alerter(self.redis_client)

    def process_image(self, image_path, user_settings, delete_after_processing=False):
        logging.info(f"Starting to process image: {image_path}")

        user = next((user for user, data in USERS.items() if data['FTP_USER'] == user_settings['FTP_USER']), None)
        
        if not user:
            logging.error(f"User not found for FTP_USER: {user_settings['FTP_USER']}")
            cleanup_files(image_path, MAIN_FTP_DIRECTORY)
            return

        if not self.get_armed_status(user):
            logging.info(f"System disarmed for user {user}. Discarding image: {image_path}")
            cleanup_files(image_path, MAIN_FTP_DIRECTORY)
            return

        if not is_within_working_hours(user_settings):
            logging.info(f"Image {image_path} received outside working hours. Deleting without processing.")
            cleanup_files(image_path, MAIN_FTP_DIRECTORY)
            return

        detections, image = self.object_detector.detect_objects(image_path, user_settings)
        if detections is None or image is None:
            logging.error(f"Failed to process image: {image_path}")
            cleanup_files(image_path, MAIN_FTP_DIRECTORY)
            return

        detected_objects = self.get_detected_objects(detections, user_settings)

        if detected_objects:
            if SAVE_POSITIVE_PHOTOS:
                save_positive_photo(image_path, user_settings['FTP_USER'], POSITIVE_PHOTOS_DIRECTORY)

            marked_image = draw_detections(image.copy(), detections)
            marked_image = add_watermark(marked_image, user_settings)
            marked_image_path = image_path.replace('.jpg', '_marked.jpg')
            cv2.imwrite(marked_image_path, marked_image)

            detection_message = f"Detected: {', '.join(detected_objects)}"
            self.telegram_bot.send_image(user_settings['TELEGRAM_CHAT_ID'], marked_image_path, detection_message)
            
            self.signl4_alerter.send_alert(marked_image_path, detection_message, user_settings)

            logging.info(f"{detection_message} in {image_path}. Marked image sent to Telegram and SIGNL4 (if configured).")

            cleanup_files(marked_image_path, MAIN_FTP_DIRECTORY)
        else:
            logging.info(f"No relevant objects detected in {image_path}.")
        
        if delete_after_processing:
            cleanup_files(image_path, MAIN_FTP_DIRECTORY)
            logging.info(f"Deleted processed file: {image_path}")
        else:
            logging.info(f"Retained processed file: {image_path}")

        logging.info(f"Finished processing image: {image_path}")

    def get_armed_status(self, user):
        key = f"{REDIS_ARMED_KEY_PREFIX}{user}"
        status = self.redis_client.get(key)
        if status is None:
            logging.info(f"Armed status for user {user} not found in Redis, using default from config.")
            return USERS[user]['ARMED']
        else:
            logging.info(f"Retrieved armed status for user {user} from Redis: {status.lower() == 'true'}")
            return status.lower() == 'true'

    def set_armed_status(self, user, status):
        key = f"{REDIS_ARMED_KEY_PREFIX}{user}"
        self.redis_client.set(key, str(status).lower())

    def get_detected_objects(self, detections, user_settings):
        detected_objects = []
        if user_settings['ENABLE_PERSON_DETECTION'] and detections['person']:
            detected_objects.append('person')
        if user_settings['ENABLE_VEHICLE_DETECTION'] and detections['vehicle']:
            detected_objects.append('vehicle')
        if user_settings['ENABLE_ANIMAL_DETECTION'] and detections['animal']:
            detected_objects.append('animal')
        return detected_objects

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    processor = ImageProcessor()
    
    # Here you would typically set up any necessary connections, start threads, etc.
    # For example, starting the Telegram bot:
    processor.telegram_bot.start()

    # In a real application, you might have a loop here to continuously process images
    # or integrate with the FTP server to process images as they are received

if __name__ == "__main__":
    main()