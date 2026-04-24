from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

client = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017"))
db = client["financegroup"]

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    result = db['users'].insert_one(data)
    return jsonify({'id': str(result.inserted_id)}), 201

if __name__ == '__main__':
    app.run(debug=True)