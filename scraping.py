import datetime
import random
import time

from config import db_client
import json
from instagrapi import Client


class IgParser:
    @staticmethod
    def try_execute(gen):
        try:
            return gen
        except Exception as e:
            print(e)
            return iter(())

    def __init__(self):
        self.__clients = {}
        self.__path_cred = None
        self.__db = db_client

    def login(self, path):
        self.__path_cred = path
        with open(path, encoding='utf-8') as f:
            json_cred = json.load(f)

        for account in json_cred:
            self.__clients[json_cred[account]['login']] = {"client": Client(), 'active': False}
            self.__clients[json_cred[account]['login']]["client"].login(json_cred[account]['login'],
                                                                        json_cred[account]['password'])

    def polling(self):
        @self.try_execute
        def scrape_followers():
            followers = client.user_followers(user_id=user_id)
            for id_ in followers:
                if id_ not in existed_users_ids:
                    parsed_users_ids.add((id_, followers[id_].username))
            yield f"Parsed {len(followers)} followers. Sleeping for about 2 min"
            time.sleep(random.randint(60, 120))

        @self.try_execute
        def scrape_medias():
            medias = client.user_medias(user_id=int(user_id), amount=27)
            yield f"Found {min(len(medias), 27)} medias"

            for i in range(min(len(medias), 27)):
                likers = client.media_likers(medias[i].id)

                for user in likers:
                    if user.pk not in existed_users_ids:
                        parsed_users_ids.add((user.pk, user.username))

                yield f"Parsed media #{i}. Sleeping for about 45 sec"
                time.sleep(random.randint(30, 60))

        @self.try_execute
        def scrape_taggers():
            medias = client.usertag_medias(user_id=int(user_id), amount=300)
            for i in range(min(len(medias), 300)):
                for media in medias:
                    if media.user.pk not in existed_users_ids:
                        parsed_users_ids.add((media.user.pk, media.user.username))
            yield f"Found {len(medias)} taggers"

        def save_results():

            stats = {
                'Parsed today': parsed_today,
                'Unique parsed today': len(parsed_users_ids),
                'Overall parsed': influencer['stats']['Overall parsed'] + len(parsed_users_ids)
            }

            self.__db['ig_users_parser']['influencers'].update_one({'username': influencer['username']},
                                                                   {"$set": {"stats": stats,
                                                                             "parsed": True,
                                                                             "datetime": datetime.datetime.now()}}
                                                                   )

        yield "Connecting db..."

        influencers_collection = self.__db['ig_users_parser']['influencers']
        parsed_users = self.__db['ig_users_parser']['parsed_users']
        existed_users_ids = set([(user['id']) for user in parsed_users.find({})])
        yield "Done"

        while True:
            influencers = influencers_collection.find({'parsed': False})
            for influencer in influencers:

                yield f'Processing link https://instagram.com/{influencer["username"]}'

                client = self.__clients[random.choice(list(self.__clients.keys()))]["client"]
                parsed_users_ids = set()

                user_id = client.user_id_from_username(influencer['username'])

                yield 'Scrapping followers...'

                for upd in scrape_followers():
                    yield upd

                yield 'Done. Scrapping medias likers...'

                for upd in scrape_medias():
                    yield upd

                yield 'Done. Scrapping taggers...'
                for upd in scrape_taggers():
                    yield upd

                yield 'Done. Saving results...'

                parsed_today = len(parsed_users_ids)

                parsed_users_ids = parsed_users_ids.difference(existed_users_ids)
                documents = [
                    {'id': id_,
                     'username': username,
                     'category': 'fashion|girls',
                     'parsed_from': influencer['username'],
                     'datetime': datetime.datetime.now()}
                    for
                    (id_, username) in parsed_users_ids]

                parsed_users.insert_many(documents)
                save_results()

                yield 'Saved successfully. Sleeping for 20 min...'
                time.sleep(20 * 60)

            time.sleep(10)
