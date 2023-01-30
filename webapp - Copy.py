
from flask import Flask, render_template,request, jsonify,redirect 
import json
from pymongo import MongoClient
from datetime import datetime, timedelta


with open('config.json') as config_file:
    config = json.load(config_file)


# Connect to MongoDB
uri = config['uri']
client = MongoClient(uri)
db = client[config['database']]
incubator = db[config['collection']]

app = Flask(__name__, static_folder='static')

def get_last_logged_record():
    last_record = incubator.find_one(sort=[("Time", -1)])
    last_logged_record_time = datetime.strptime(get_last_logged_record(), "%m-%d-%Y %H:%M")  
    timePassed = (datetime.now() - last_logged_record_time)
    timePassed = timePassed.total_seconds()
    if last_record is not None:
        return timePassed
    else:
        return -1

