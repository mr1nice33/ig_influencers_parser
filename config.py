import pymongo
from pymongo.server_api import ServerApi
import os

ID_TELEGRAM_CHAT = 1736337003

os.environ['MONGODB_CREDENTIALS'] = ''
os.environ['TG_BOT_TOKEN'] = ''

db_client = pymongo.MongoClient(
    f"mongodb+srv://{os.getenv('MONGODB_CREDENTIALS')}@cluster0.ybjnnvs.mongodb.net/?retryWrites=true&w=majority",
    server_api=ServerApi('1'))
