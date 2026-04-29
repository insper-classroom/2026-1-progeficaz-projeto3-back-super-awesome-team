from pymongo import MongoClient
import os

client = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017"))
mongo = client["financegroup"]
