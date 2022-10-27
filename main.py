import telebot
import os
import config
from threading import Thread
from scraping import IgParser
import datetime

bot = telebot.TeleBot(os.getenv('TG_BOT_TOKEN'), parse_mode=None, threaded=False)

links_db = config.db_client['ig_users_parser']['influencers']


@bot.message_handler(func=lambda message: 'instagram.com' in message.text and 'https://' in message.text)
def process_url(message):
    if message.from_user.id == config.ID_TELEGRAM_CHAT:

        correct_link = message.text + '/' if message.text[-1] != '/' else message.text
        short_link = correct_link.split('/')
        username = short_link[3].split('?')[0]

        if links_db.count_documents({'username': username}) == 0:

            links_db.insert_one({'username': username, 'parsed': False,
                                 'stats': {
                                     'Parsed today': 0,
                                     'Unique parsed today': 0,
                                     'Overall parsed': 0},
                                 'datetime': datetime.datetime.now()})

            bot.send_message(config.ID_TELEGRAM_CHAT, 'Added')
        else:
            bot.send_message(config.ID_TELEGRAM_CHAT, 'Link is already in db')


@bot.message_handler(commands=['stats'])
def get_stats():
    pass


def scrapping_updates():
    print('Login ...')
    parser = IgParser()
    parser.login('credentials.json')
    print('Login done')

    for update_message in parser.polling():
        bot.send_message(config.ID_TELEGRAM_CHAT, update_message)


if __name__ == '__main__':
    threads = [
        Thread(target=bot.polling, args=()),
        Thread(target=scrapping_updates, args=[])
    ]

    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
