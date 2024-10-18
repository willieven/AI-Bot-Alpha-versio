import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import logging

class TelegramBot:
    def __init__(self, token):
        self.bot = telepot.Bot(token)
        MessageLoop(self.bot, self.handle_message).run_as_thread()

    def create_keyboard(self):
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='/arm'), KeyboardButton(text='/disarm')],
            [KeyboardButton(text='/status'), KeyboardButton(text='/autoarm')]
        ])

    def handle_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            self.handle_command(msg)

    def handle_command(self, msg):
        # Implementation of command handling

    def send_image(self, chat_id, image_path, caption):
        try:
            with open(image_path, 'rb') as image_file:
                self.bot.sendPhoto(chat_id, image_file, caption=caption)
            logging.info(f"Image sent successfully: {image_path}")
        except Exception as e:
            logging.error(f"Error sending image to Telegram: {str(e)}")

    def send_message(self, chat_id, text, keyboard=None):
        self.bot.sendMessage(chat_id, text, reply_markup=keyboard)