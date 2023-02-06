
import time
import RPi.GPIO as GPIO
from pymongo import MongoClient
from datetime import datetime, timedelta
import json
import board
import busio
import adafruit_ahtx0

with open('config.json') as config_file:
    config = json.load(config_file)

start_date = datetime.strptime(config['start_date'], '%Y-%m-%d')

# Connect to MongoDB
uri = config['uri']
client = MongoClient(uri)
db = client[config['database']]
incubator = db[config['collection']]

i2c = busio.I2C(board.SCL, board.SDA)
aht = adafruit_ahtx0.AHTx0(i2c)


# Set the sensor type (DHT22) and the GPIO pin number


# Set the relay pin number
egg_turner_relay_pin = 6
heat_relay_pin = 18
humidifier_relay_pin = 27

# Set the interval for logging data and turning on the relay (in seconds)
log_interval = config['log_interval']
relay_interval = config['relay_interval']
roll_interval = config['roll_interval']
last_relay_on = config['last_relay_on']
dataLogged = config['dataLogged']
temperature_relay_status = config['temperature_relay_status']
humidity_relay_status = config['humidity_relay_status']
day_in_cycle = config['day_in_cycle']


# Set the temperature and humidity thresholds
temperature_threshold = 101
humidity_threshold = 55

# Initialize the GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(egg_turner_relay_pin,GPIO.OUT)
GPIO.setup(heat_relay_pin,GPIO.OUT)
GPIO.setup(humidifier_relay_pin,GPIO.OUT)

      


last_read_time = None
last_read_value = (None, None)

def read_sensor_data():
    global last_read_time
    global last_read_value
    if last_read_time is None or time.time() - last_read_time >= 4:
        # Read the humidity and temperature
        temperature = aht.temperature
        humidity = aht.relative_humidity
        if humidity is not None and temperature is not None:
            temperature = (temperature * 9/5) + 32
            last_read_value = round(temperature,1), round(humidity,1)
            last_read_time = time.time()
        else:
            print('Failed to read data from sensor')
            last_read_value = None, None
            last_read_time = None
    return last_read_value


def log_data(temperature, humidity, last_relay_on,temperature_relay_status,humidity_relay_status,day_in_cycle):
    # Create a data dictionary
    data = {
        'Time': time.strftime("%m-%d-%Y %H:%M"),
        'Temperature(F)': temperature,
        'Temperature Relay Status': temperature_relay_status,
        'Humidity(%)': humidity,
        'Humidity Relay Status': humidity_relay_status,
        'Last Egg Turn': last_relay_on.strftime("%m-%d-%Y %I:%M %P"),
        'Day in Egg Cycle' : day_in_cycle
    }
    # Insert the data into the incubator collection
    incubator.insert_one(data)
    

def eggTurner():
    current_time = datetime.now()
    global last_relay_on
    day_in_cycle = day()
    if day_in_cycle <18:
        if last_relay_on is None:
            GPIO.output(egg_turner_relay_pin, GPIO.LOW)
            last_relay_on = current_time
        if GPIO.input(egg_turner_relay_pin) == 1:
            if current_time - last_relay_on >= timedelta(seconds=relay_interval):
                # Turn on the relay for 2 minutes
                GPIO.output(egg_turner_relay_pin, GPIO.LOW)
                last_relay_on = current_time
        elif GPIO.input(egg_turner_relay_pin) == 0:        
            if current_time - last_relay_on >= timedelta(seconds=roll_interval):
                GPIO.output(egg_turner_relay_pin, GPIO.HIGH)
                
    return last_relay_on


def control():
    global humidifier_relay_pin
    temperature, humidity = read_sensor_data()
    
    global temperature_relay_status
    global humidity_relay_status

    if temperature <= (temperature_threshold - 1):
        # Turn on the heat source
        GPIO.output(heat_relay_pin, GPIO.LOW)
        if GPIO.input(heat_relay_pin) == 0:
            temperature_relay_status = "ON"
        else:
            print("HEAT GPIO not setting to low or ON")

    elif temperature > temperature_threshold:
        # Turn off the heat source
        GPIO.output(heat_relay_pin, GPIO.HIGH)
        if GPIO.input(heat_relay_pin) == 1: 
            temperature_relay_status = "OFF"
        else:
            print("HEAT GPIO not setting to High or OFF")

    # Check if the humidity is above the threshold
    if humidity < (humidity_threshold-5):
        # Turn off the humidifier
        GPIO.output(humidifier_relay_pin, GPIO.LOW)
        if GPIO.input(humidifier_relay_pin) == 0:
            humidity_relay_status = "ON"
        else:
            print("HUMIDITY GPIO not setting to low or ON")

    else:
        # Turn off the humidifier
        GPIO.output(humidifier_relay_pin, GPIO.HIGH)
        if GPIO.input(humidifier_relay_pin) == 1:
            humidity_relay_status = "OFF"
        else:
             print("HUMIDITY GPIO not setting to HIGH or OFF")
        
    

def day():
    global humidity_threshold
    current_date = datetime.now()
    total_days = 21
    day_in_cycle = (current_date - start_date).days % total_days
    if day_in_cycle >= 18:
        humidity_threshold = 75
    return day_in_cycle





def read_and_log_data():
    global dataLogged
    try:
        while True:
            day_in_cycle = day()
            control()
            last_relay_on = eggTurner()
            temperature, humidity = read_sensor_data()
            log_data(temperature, humidity, last_relay_on,temperature_relay_status,humidity_relay_status, day_in_cycle)
            print("Last Egg roll: "+last_relay_on.strftime("%m-%d-%Y %I:%M %P"))
            print("Last Temperature Reading: "+str(temperature)+"F  Last Temperature Relay: "+temperature_relay_status)
            print("Last Humidity Reading: "+str(humidity)+"%  Last Humidity Relay: "+humidity_relay_status)
            temperature2 = aht.temperature
            humidity2 = humidity = aht.relative_humidity
            print("Temperature: {:.1f}°C".format(temperature2))
            print("Humidity: {:.1f}%".format(humidity2))
            print(" ")
            print(" ")
            time.sleep(300)

    except KeyboardInterrupt:
        pass
    finally:
        # Clean up the GPIO pins
        GPIO.cleanup()
        # Close the MongoDB connection
        client.close()
  


if __name__ == "__main__":
    read_and_log_data()
