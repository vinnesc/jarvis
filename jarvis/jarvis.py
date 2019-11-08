import os
import time
import logging
import json
import requests
import sys
import random
from threading import Timer

import pyimgur
from telepot import Bot, glance
from telepot.loop import MessageLoop

logger = logging.getLogger()
handler = logging.FileHandler('chat.log')
console = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(console)
logger.setLevel(logging.INFO)


vibe_checks = ['images/vibe_check_0.jpg', 'images/vibe_check_1.jpg', 'images/vibe_check_2.jpg']

class Jarvis:
    def __init__(self):
        with open('secrets.json', mode='r') as f:
            self.secrets = json.load(f)
        self.bot = Bot(self.secrets['telegram'])
        self.img_uploader = pyimgur.Imgur(self.secrets['imgur']['client_id'], self.secrets['imgur']['client_secret'])
        self.last_update = 0
    
    def handle_message(self, message):
        content_type, chat_type, chat_id = glance(message)
        message_id = message['message_id']
        user =  message['from']
        chat = message['chat']
        
        if content_type == 'text':
            logger.info('{user}: {message}'.format(user=user['username'], message=message['text']))
            if 'el edus sabe' in message['text'] or 'el carmelos sabe' in message['text'] or 'el vinnys sabe' in message['text']:
                is_sabe = random.randint(0, 1)
                sabe = 'sabe' if is_sabe else 'no sabe'
                self.bot.sendMessage(chat['id'], '{sabe} @{user}'.format(user=user['username'], sabe=sabe))
            elif message['text'] == 'vibe check':
                vibe_check = random.randint(0, len(vibe_checks) - 1)
                with open(vibe_checks[vibe_check], 'rb') as f:
                    self.bot.sendPhoto(chat['id'], f)
                    logger.info('vibe_check read.')
        elif content_type == 'photo':
            photos = message['photo']
            photo = photos[0] # Take lowest resolution

            photo_file = self.bot.getFile(photo['file_id'])
            photo_url = 'https://api.telegram.org/file/bot{token}/{file_path}'.format(token=self.secrets['telegram'], file_path=photo_file['file_path'])
            photo_request = requests.get(photo_url)
            if photo_request.status_code == 200:
                photo_path = 'images/' + photo['file_id'] + '.jpg'
                with open(photo_path, 'wb') as f:
                    f.write(photo_request.content)
                    logger.info('Image saved.')
                    self.bot.sendMessage(chat['id'], 'Me he guardado la foto.')
                
                uploaded_image = self.img_uploader.upload_image(photo_path)
                self.bot.sendMessage(chat['id'], 'Toma un link (se borra en 30 segundos): {link}'.format(link=uploaded_image.link))
                
                logger.info('Image uploaded.')
                
                deleter = Timer(30.0, self.delete_image, [uploaded_image])
                deleter.start()
            else:
                logger.error('Unable to download photo.')
    
    def delete_image(self, image):
        image.delete()
        logger.info('Image deleted.')

    def run(self):
        print('Running Jarvis...')
        MessageLoop(self.bot, handle=self.handle_message).run_as_thread()


def main():
    jarvis = Jarvis()

    jarvis.run()
    while True:
        time.sleep(10)