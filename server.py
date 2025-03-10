import threading
import json
import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt

app = Flask(__name__)

# Global variables to store sensor data
switch_value = 0  # 0 (off) or 1 (on)
updated_switch_value = 0  # Updated switch value
mc_data = {"battery": 70, "status": "Unknown"}  # Microcontroller data
amb_data = {"temperature": 0, "humidity": 0, "pressure": 0}  # Ambient sensor data

# Global lists for ambient sensor historical data
amb_history_temperature = []
amb_history_humidity = []
amb_history_pressure = []

# MQTT configuration for HiveMQ Cloud (or other broker)
MQTT_BROKER = "152.74.19.95"
MQTT_PORT = 10273
MQTT_USER = "wester"
MQTT_PASS = "2005483"

# Topics
TOPIC_USER_VARIABLES = "myapp/user/control"          # For publishing switch updates
TOPIC_MICROCONTROLLER = "myapp/microcontroller/status"   # For receiving microcontroller data
TOPIC_AMB_VARS = "myapp/microcontroller/amb_vars"        # Ambient sensor topic

# Initialize SocketIO with the Flask app
socketio = SocketIO(app)  # This is where SocketIO is defined

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected to MQTT broker with result code " + str(rc))
    # Subscribe to topics for receiving data
    client.subscribe(TOPIC_MICROCONTROLLER)
    client.subscribe(TOPIC_AMB_VARS)

def on_message(client, userdata, msg):
    global updated_switch_value, mc_data, amb_data, amb_history_temperature, amb_history_humidity, amb_history_pressure
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current timestamp
        if msg.topic == TOPIC_MICROCONTROLLER:
            mc_data["battery"] = data.get("battery", mc_data["battery"])
            mc_data["status"] = data.get("status", mc_data["status"])
            print("Updated microcontroller data:", mc_data)
            socketio.emit('mqtt_timestamp_update', {'timestamp': timestamp})
        elif msg.topic == TOPIC_AMB_VARS:
            new_temp = data.get("temperature", float('nan'))
            new_hum = data.get("humidity", float('nan'))
            new_pres = data.get("pressure", float('nan'))
            amb_data["temperature"] = new_temp
            amb_data["humidity"] = new_hum
            amb_data["pressure"] = new_pres
            print("Updated ambient sensor data:", amb_data)
            amb_history_temperature.append(new_temp)
            amb_history_humidity.append(new_hum)
            amb_history_pressure.append(new_pres)
            # Send the timestamp with the data
            socketio.emit('mqtt_timestamp_update', {'timestamp': timestamp})
            
    except Exception as e:
        print("Error processing MQTT message:", e)

# Setup MQTT client using the MQTT v5 callback API if supported
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
try:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
except Exception as e:
    print("No user credentials provided, skipping login")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def mqtt_loop():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print("Error connecting to MQTT broker:", e)
        print("defaulting to connect to local server")
        mqtt_client.connect("0.0.0.0", 1883, 60) # connect to local broker
    finally:
        mqtt_client.loop_forever()

@app.route("/", methods=["GET", "POST"])
def index():
    global switch_value
    if request.method == "POST":
        # Update the switch value based on form input
        switch_value = 1 if request.form.get("toggle") == "on" else 0
        payload = json.dumps({"switch": switch_value})
        print("Publishing switch value:", payload)
        # Send the timestamp with the data
        socketio.emit('mqtt_switch_update', {'switch': updated_switch_value})
        mqtt_client.publish(TOPIC_USER_VARIABLES, payload, qos=1, retain=True)
    return render_template("index.html", 
                           switch_value=switch_value, 
                           battery_level=mc_data["battery"],
                           mc_status=mc_data["status"],
                           amb_data=amb_data,
                           amb_history_temperature=amb_history_temperature,
                           amb_history_humidity=amb_history_humidity,
                           amb_history_pressure=amb_history_pressure)

if __name__ == "__main__":
    # Start the MQTT loop in a separate thread
    mqtt_thread = threading.Thread(target=mqtt_loop)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    
    # Run the Flask app (no Socket.IO auto-reload; page reload is manual)
    # app.run(debug=True, host="0.0.0.0", port=5000)
    # Run Flask with SocketIO instead of the regular app.run
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
