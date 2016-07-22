import requests
from datetime import datetime
from logging import getLogger
logger = getLogger(__name__)
from shifthelper.config import config
class TelegramInterface(object):
    url = 'https://api.telegram.org/bot{token}'

    def __init__(self, chat_id):
        bot_token = config['telegram']['token']
        self.url = self.url.format(token=bot_token)
        self.chat_id = chat_id

    def send_image(self, image):
        try:
            r = requests.post(
                self.url + '/sendPhoto',
                data={'chat_id': self.chat_id},
                files={'photo': image},
                timeout=15,
            )
        except requests.exceptions.Timeout:
            logger.exception('Telegram "send_message" timed out')
        return r

    def send_message(self, message):
        try:
            r = requests.post(
                self.url + '/sendMessage',
                data={'chat_id': self.chat_id, 'text': message},
                timeout=5,
            )
        except requests.exceptions.Timeout:
            logger.exception('Telegram "send_message" timed out')
        return r