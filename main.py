import gc
import config
import uasyncio as asyncio
import machine
import utime as time
import usocket as socket
import ustruct as struct
from umqtt.simple import MQTTClient
import json
import wifi

gc.enable()
wifi.activate()
int_err_count = 0
ping_mqtt = 0
ping_fail = 0

use_topic = config.CONFIG['DEVICE_TYPE'] + "/" + config.CONFIG['DEVICE_PLACE'] + "/" + config.CONFIG[
    'DEVICE_PLACE_NAME'] + "/"

device_topic = config.CONFIG['DEVICE_TYPE'] + "/" + config.CONFIG['DEVICE_PLACE'] + "/" + config.CONFIG[
    'DEVICE_PLACE_NAME'] + "/" + config.CONFIG['DEVICE_ID'] + "/"


def get_uptime():
    return json.dumps(time.time())


# Check Internet connection
def internet_connected(host='8.8.8.8', port=53):
    global int_err_count
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        try:
            s.connect((host, port))
            int_err_count = 0
            return True
        except Exception as e:
            print("Error Internet connect: [Exception] %s: %s" % (type(e).__name__, e))
            return False
        finally:
            s.close()


# Check Internet connection
def internet_connected(host='8.8.8.8', port=53):
    global int_err_count
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        try:
            s.connect((host, port))
            int_err_count = 0
            return True
        except Exception as e:
            print("Error Internet connect: [Exception] %s: %s" % (type(e).__name__, e))
            return False
        finally:
            s.close()


# Publish uptime
async def send_uptime():
    while True:
        print("Publish uptime ...")
        await asyncio.sleep(10)
        device_id = config.CONFIG['DEVICE_ID']
        print(device_topic + "data/uptime/%s" % device_id, "%s" % get_uptime())
        client.publish(device_topic + "data/uptime/%s" % device_id, "%s" % get_uptime())
        await asyncio.sleep(1)


def on_message(topic, msg):
    global ping_fail
    print("Topic: %s, Message: %s" % (topic, msg))

    if "/check/mqtt" in topic:
        if int(msg) == ping_mqtt:
            print("MQTT pong true...")
            ping_fail = 0
        else:
            print("MQTT pong false... (%i)" % ping_fail)

    if "/check/ping" in topic:
        send_mqtt_pong(msg)


# Pong MQTT connect
def send_mqtt_pong(pong_msg):
    print(pong_msg.decode("utf-8"))
    client.publish(device_topic + "/state/check/pong/",
                   pong_msg.decode("utf-8"))


# Check MQTT brocker
async def check_mqtt():
    global ping_fail
    global ping_mqtt
    while True:
        await asyncio.sleep(10)
        ping_mqtt = time.time()
        client.publish(device_topic + "state/check/mqtt/", "%s" % ping_mqtt)
        print("Send MQTT ping (%i)" % ping_mqtt)
        ping_fail += 1

        if ping_fail >= config.CONFIG['MQTT_CRIT_ERR']:
            print("MQTT ping false... reset (%i)" % ping_fail)
            machine.reset()

        if ping_fail >= config.CONFIG['MQTT_MAX_ERR']:
            print("MQTT ping false... reconnect (%i)" % ping_fail)
            client.disconnect()
            mqtt_reconnect()


# MQTT reconnect
def mqtt_reconnect():
    global client
    try:
        client = MQTTClient(config.CONFIG['MQTT_CLIENT_ID'],
                            config.CONFIG['MQTT_BROKER'],
                            # user=config.CONFIG['MQTT_USER'],
                            # password=config.CONFIG['MQTT_PASSWORD'],
                            port=config.CONFIG['MQTT_PORT'])

        client.DEBUG = True
        client.set_callback(on_message)
        client.connect(clean_session=True)
        if config.CONFIG['DEVICE_ID'] == config.CONFIG['DEVICE_ID_USE']:
            client.subscribe(use_topic + "#")
            print("ESP8266 is Connected to %s and subscribed to %s topic" % (
                config.CONFIG['MQTT_BROKER'], use_topic + "#"))
        else:
            client.subscribe(device_topic + "#")
            print("ESP8266 is Connected to %s and subscribed to %s topic" % (
                config.CONFIG['MQTT_BROKER'], device_topic + "#"))

        client.publish(device_topic + "info/", "%s" % [config.CONFIG['DEVICE_TYPE'], config.CONFIG['DEVICE_PLACE'],
                                                       config.CONFIG['DEVICE_PLACE_NAME'], config.CONFIG['DEVICE_ID']])
    except Exception as e:
        print("Error in MQTT reconnection: [Exception] %s: %s" % (type(e).__name__, e))


# Check MQTT message
async def check_message():
    while True:
        await asyncio.sleep(1)
        print("Check message...")
        try:
            client.check_msg()
        except Exception as e:
            print("Error in mqtt check message: [Exception] %s: %s" % (type(e).__name__, e))


mqtt_reconnect()
try:
    loop = asyncio.get_event_loop()
    loop.create_task(send_uptime())
    loop.create_task(check_message())
    loop.create_task(check_mqtt())
    loop.run_forever()
except Exception as e:
    print("Error: [Exception] %s: %s" % (type(e).__name__, e))
    time.sleep(60)
    machine.reset()
