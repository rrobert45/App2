
from flask import Flask, render_template,request, jsonify,redirect 
import json
from pymongo import MongoClient


with open('config.json') as config_file:
    config = json.load(config_file)


# Connect to MongoDB
uri = config['uri']
client = MongoClient(uri)
db = client[config['database']]
incubator = db[config['collection']]

app = Flask(__name__, static_folder='static')


@app.route("/")
def index():
        cursor = incubator.find().limit(250).sort("Time", -1)
        historical_data = []
        for data in cursor:
            historical_data.append({
                'Time': data['Time'],
                'Temperature(F)': data['Temperature(F)'],
                'Temperature Relay Status': data['Temperature Relay Status'],
                'Humidity(%)': data['Humidity(%)'],
                'Humidity Relay Status': data['Humidity Relay Status'],
                'Last Egg Turn': data['Last Egg Turn'],
                'Day in Egg Cycle' : data['Day in Egg Cycle']
            })
        data = {
            
            'historical_data': historical_data,

        }
        return render_template('index.html',data=data)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)