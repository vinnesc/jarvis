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


class Jarvis:
    def __init__(self, secrets, bot_api, photo_api, music_api):
        self.secrets = secrets
        self.bot_api = bot_api
        self.photo_api = photo_api
        self.music_api = music_api
        self.saves_photos = False

        self.vibe_checks = ['images/vibe_check_0.jpg', 'images/vibe_check_1.jpg', 'images/vibe_check_2.jpg']

    def vibe_check(self):
        vibe_check = random.randint(0, len(self.vibe_checks) - 1)
            
        with open(self.vibe_checks[vibe_check], 'rb') as f:
            logger.info('vibe_check read.')
            return f
    
    def lottery(self, lottery_type):
        if lottery_type == 'sabe':
            is_sabe = random.randint(0, 1)
            sabe = 'sabe' if is_sabe else 'no sabe'
            return sabe           

    def sing(self, song, user):
        tracks_first = self.music_api.user_playlist_tracks(user='rolusito', playlist_id='2lDQRaS5bz2hiW3Ys9khZU', limit=100)
        tracks_second = self.music_api.user_playlist_tracks(user='rolusito', playlist_id='2lDQRaS5bz2hiW3Ys9khZU', offset=100)
        
        found = False
        for item in tracks_first['items']:
            if song in item['track']['name'].lower():
                logger.info('Cantando {song}'.format(song=song))
                if not item['track']['preview_url']:
                    return '[{song_name}]({song_link})'.format(song_name=item['track']['name'], song_link=item['track']['external_urls']['spotify'])
                else:
                    return '[{song_name}]({song_link})'.format(song_name=item['track']['name'], song_link=item['track']['preview_url'])
            found = True
        
        for item in tracks_second['items']:
            if song in item['track']['name'].lower():
                logger.info('Cantando {song}'.format(song=song))
                if not item['track']['preview_url']:
                    return '[{song_name}]({song_link})'.format(song_name=item['track']['name'], song_link=item['track']['external_urls']['spotify'])
                else:
                    return '[{song_name}]({song_link})'.format(song_name=item['track']['name'], song_link=item['track']['preview_url'])
            found = True
        
        if not found:
            return 'Esa no la tengo @{user}'.format(user=user['username'])
        

    def handle_command(self, chat, user, text):
        if 'sabe' in text:
            sabe = self.lottery('sabe')
            self.bot_api.sendMessage(chat['id'], '{sabe} @{user}'.format(user=user['username'], sabe=sabe))
        elif text == 'vibe check':
            vibe_check = self.vibe_check()
            self.bot_api.sendPhoto(chat['id'], vibe_check)
        elif 'cantate' in text:
            song = text[8:]
            response = self.sing(song, user)
            self.bot_api.sendMessage(chat['id'], response, parse_mode='Markdown')
        elif text == 'guarda foto':
            self.saves_photos = True
            self.bot_api.sendMessage(chat['id'], 'Guardo la próxima foto', parse_mode='Markdown')


    def save_photo(self, chat, photo):
        photo_file = self.bot_api.getFile(photo['file_id'])
        photo_url = 'https://api.telegram.org/file/bot{token}/{file_path}'.format(token=self.secrets['telegram'], file_path=photo_file['file_path'])
        photo_request = requests.get(photo_url)

        if photo_request.status_code == 200:
            photo_path = 'images/' + photo['file_id'] + '.jpg'
            with open(photo_path, 'wb') as f:
                f.write(photo_request.content)
                logger.info('Image saved.')
                self.bot_api.sendMessage(chat['id'], 'Me he guardado la foto.')
            
            uploaded_image = self.photo_api.upload_image(photo_path)
            self.bot_api.sendMessage(chat['id'], 'Toma un link (se borra en 30 segundos): {link}'.format(link=uploaded_image.link))
            
            logger.info('Image uploaded.')
            
            deleter = Timer(30.0, self.delete_photo, [uploaded_image])
            deleter.start()
        else:
            self.bot_api.sendMessage(chat['id'], 'No me la he podido guardar :(')
            logger.error('Unable to download photo.')
        
        self.saves_photos = False


    def handle_message(self, message):
        content_type, chat_type, chat_id = glance(message)
        message_id = message['message_id']
        user =  message['from']
        chat = message['chat']
        
        if content_type == 'text':
            text = message['text'].lower()
            logger.info('{user}: {message}'.format(user=user['username'], message=text))
            
            self.handle_command(chat, user, text)
        elif content_type == 'photo' and self.saves_photos:
            photos = message['photo']
            photo = photos[0] # Take lowest resolution

            self.save_photo(chat, photo)

    
    def delete_photo(self, image):
        image.delete()
        logger.info('Image deleted.')

    def run(self):
        print('Running Jarvis...')
        MessageLoop(self.bot_api, handle=self.handle_message).run_as_thread()


def load_secrets():
    with open('secrets.json', mode='r') as f:
        return json.load(f)


def setup_apis(secrets):
    bot_secrets = secrets['telegram']
    photo_secrets = secrets['imgur']
    music_secrets = secrets['spotify']

    bot = Bot(bot_secrets)

    photo = pyimgur.Imgur(photo_secrets['client_id'], photo_secrets['client_secret'])

    client_credentials_manager = SpotifyClientCredentials(client_id=music_secrets['client_id'], client_secret=music_secrets['client_secret']) 
    music = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    music.trace = False

    return bot, photo, music

def main():
    secrets = load_secrets()
    bot_api, photo_api, music_api = setup_apis(secrets)

    jarvis = Jarvis(secrets, bot_api, photo_api, music_api)

    jarvis.run()
    while True:
        time.sleep(10)