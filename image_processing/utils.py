import os
import logging
from datetime import datetime

def is_within_working_hours(user_settings):
    current_time = datetime.now().time()
    start_time = datetime.strptime(user_settings['WORKING_START_TIME'], '%H:%M').time()
    end_time = datetime.strptime(user_settings['WORKING_END_TIME'], '%H:%M').time()
    
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    else:  # Working hours go past midnight
        return current_time >= start_time or current_time <= end_time

def cleanup_files(file_path, base_directory):
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.info(f"Deleted file: {file_path}")
    
    directory = os.path.dirname(file_path)
    while directory != base_directory:
        if not os.listdir(directory):
            os.rmdir(directory)
            logging.info(f"Removed empty directory: {directory}")
            directory = os.path.dirname(directory)
        else:
            break

def save_positive_photo(image_path, username, positive_photos_directory):
    try:
        user_positive_dir = os.path.join(positive_photos_directory, username)
        os.makedirs(user_positive_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}_{os.path.basename(image_path)}"
        new_path = os.path.join(user_positive_dir, new_filename)

        shutil.copy2(image_path, new_path)
        logging.info(f"Original image with positive detection saved: {new_path}")
    except Exception as e:
        logging.error(f"Error saving original image with positive detection: {str(e)}")