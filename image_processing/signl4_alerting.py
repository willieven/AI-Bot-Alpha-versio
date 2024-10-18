import requests
import logging
import time

class SIGNL4Alerter:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.ALERT_COOLDOWN = 300  # 5 minutes

    def get_lock(self, lock_name, expire=60):
        return self.redis_client.set(f"lock:{lock_name}", "locked", nx=True, ex=expire)

    def get_last_alert_time(self, user):
        return self.redis_client.get(f"last_alert:{user}")

    def set_last_alert_time(self, user, timestamp):
        self.redis_client.set(f"last_alert:{user}", timestamp)

    def send_alert(self, image_path, detection_message, user_settings):
        if 'SIGNL4_SECRET' not in user_settings or not user_settings['SIGNL4_SECRET']:
            logging.info(f"Skipping SIGNL4 alert for {user_settings['FTP_USER']} - No SIGNL4 secret configured")
            return

        current_time = time.time()
        ftp_user = user_settings['FTP_USER']
        
        lock_name = f"signl4_alert:{ftp_user}"
        if not self.get_lock(lock_name, expire=self.ALERT_COOLDOWN):
            logging.info(f"Skipping SIGNL4 alert for {ftp_user} - Rate limited or another alert is being processed")
            return

        try:
            last_alert = self.get_last_alert_time(ftp_user)
            if last_alert and current_time - float(last_alert) < self.ALERT_COOLDOWN:
                logging.info(f"Skipping SIGNL4 alert for {ftp_user} due to rate limiting")
                return

            files = {
                'Image': ('image.jpg', open(image_path, 'rb'), 'image/jpeg')
            }
            data = {
                'Title': f"Intrusion Detection Alert for {ftp_user}",
                'Message': detection_message,
                'Severity': 'High'
            }

            response = requests.post(
                user_settings['SIGNL4_SECRET'],
                files=files,
                data=data
            )

            if response.status_code == 200:
                logging.info(f"SIGNL4 alert sent successfully for {ftp_user}")
                self.set_last_alert_time(ftp_user, str(current_time))
            else:
                logging.error(f"Failed to send SIGNL4 alert for {ftp_user}: {response.text}")

        except Exception as e:
            logging.error(f"Error sending SIGNL4 alert for {ftp_user}: {str(e)}")
        finally:
            if 'Image' in files and hasattr(files['Image'][1], 'close'):
                files['Image'][1].close()