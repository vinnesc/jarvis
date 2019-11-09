import os
import time
import logging
import json
import requests
import sys
import random
from threading import Timer

import pyimgur

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials 

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
        self.saves_photos = False

        client_credentials_manager = SpotifyClientCredentials(client_id=self.secrets['spotify']['client_id'], client_secret=self.secrets['spotify']['client_secret']) 
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        self.spotify.trace = False

    def handle_message(self, message):
        content_type, chat_type, chat_id = glance(message)
        message_id = message['message_id']
        user =  message['from']
        chat = message['chat']
        text = message['text'].lower()
        
        if content_type == 'text':
            logger.info('{user}: {message}'.format(user=user['username'], message=message['text']))
            if 'edus sabe' in text or 'carmelos sabe' in text or 'vinnys sabe' in text:
                is_sabe = random.randint(0, 1)
                sabe = 'sabe' if is_sabe else 'no sabe'
                self.bot.sendMessage(chat['id'], '{sabe} @{user}'.format(user=user['username'], sabe=sabe))
            elif text == 'vibe check':
                vibe_check = random.randint(0, len(vibe_checks) - 1)
                with open(vibe_checks[vibe_check], 'rb') as f:
                    self.bot.sendPhoto(chat['id'], f)
                    logger.info('vibe_check read.')
            elif 'cantate' in text:
                song = text[8:]

                tracks_first = self.spotify.user_playlist_tracks(user='rolusito', playlist_id='2lDQRaS5bz2hiW3Ys9khZU', limit=100)
                tracks_second = self.spotify.user_playlist_tracks(user='rolusito', playlist_id='2lDQRaS5bz2hiW3Ys9khZU', offset=100)
                
                found = False
                for item in tracks_first['items']:
                    if song in item['track']['name'].lower():
                        logger.info('Cantando {song}'.format(song=song))
                        if not item['track']['preview_url']:
                            self.bot.sendMessage(chat['id'], '[{song_name}]({song_link})'.format(song_name=item['track']['name'], song_link=item['track']['external_urls']['spotify']), parse_mode='Markdown')
                        else:
                            self.bot.sendMessage(chat['id'], '[{song_name}]({song_link})'.format(song_name=item['track']['name'], song_link=item['track']['preview_url']), parse_mode='Markdown')
                    found = True
                
                for item in tracks_second['items']:
                    print(item['track']['name'])
                    if song in item['track']['name'].lower():
                        logger.info('Cantando {song}'.format(song=song))
                        if not item['track']['preview_url']:
                            self.bot.sendMessage(chat['id'], '[{song_name}]({song_link})'.format(song_name=item['track']['name'], song_link=item['track']['external_urls']['spotify']), parse_mode='Markdown')
                        else:
                            self.bot.sendMessage(chat['id'], '[{song_name}]({song_link})'.format(song_name=item['track']['name'], song_link=item['track']['preview_url']), parse_mode='Markdown')
                    found = True
                
                if not found:
                    self.bot.sendMessage(chat['id'], 'Esa no la tengo @{user}'.format(user=user['username']))
                
            elif text == 'guarda foto':
                self.saves_photos = True
        elif content_type == 'photo' and self.saves_photos:
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
            
            self.saves_photos = False
    
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