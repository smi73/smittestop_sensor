from threading import Thread
from flask import Flask, render_template, url_for, Response
from collections import defaultdict
import time
import lib.en_rx_service
import traceback
import logging
import os
import json
import requests


#from beacontools import BeaconScanner, ExposureNotificationFrame
#from beacontools import parse_packet




global rssi_db
global rssi_average_last_100_db
global lastTimestamp_db

rssi_db = defaultdict(list)
lastTimestamp_db = {}
rssi_average_last_100_db = {}

local = False

if "DEBUG" in os.environ:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if local:
    root_path = '/home/pi/projects/python/exposure'
else:
    root_path = '/usr/app/'

def join_data():
    test = {b'9oi\tC\xd3\x12&j\x8b\xb7\xf6Yw\xedH': [-78, -89], b'\x86\xba\x1fl#\xb3\xe42\x87<d\xac2\xc0\x12\xcc': [-68], b'\x15\xad\x9f\x1a\x8dp\x1a\x9fb\x8a:5\x1b\xd2H\x15': [-72]}
    return test.keys()

def callback(bt_addr, rssi, packet, additional_info):
    #print("<%s, %d> %s %s" % (bt_addr, rssi, packet, additional_info))
    #print("<%d> %s" % (rssi, packet))
    rssi_db[packet.identifier].append(rssi)
    secondsSinceEpoch = time.time()
    lastTimestamp_db[packet.identifier] = secondsSinceEpoch
    rssi_average_last_100_db[packet.identifier] = calc_average_rssi(packet.identifier)
    oldKey = getKeyForFirstTimestampOlderThan5Sec()
    if oldKey is not None:
        deleteKeyInDbs(oldKey)

def get_number_of_devices():
    return len(rssi_db)

def get_local_devices():
    return rssi_db.keys()

def calc_average_rssi(key):
    my_rssi = rssi_db[key]
    last_up_to_100_list = my_rssi[-100:]
    my_average = sum(last_up_to_100_list) / len(last_up_to_100_list) 
    return my_average

def getKeyForFirstTimestampOlderThan5Sec():
    for x in lastTimestamp_db:
        secondsSinceEpoch = time.time()
        deltaTime = secondsSinceEpoch - lastTimestamp_db[x]
        #print(deltaTime)
        if deltaTime > 5.0:
            return x
    return None
    
def deleteKeyInDbs(key):
    rssi_db.pop(key)
    lastTimestamp_db.pop(key)
    rssi_average_last_100_db.pop(key)

def get_average_rssi():
    return rssi_average_last_100_db

def get_nmb_of_close_devices():
    j = rssi_average_last_100_db.values()
    #logging.info("rssi_average_last_100_db: %s", j)
    j2 = [i for i in j if i >= -60.0]
    myLen = len(j2)
    return myLen

def get_nmb_of_far_devices():
    return get_number_of_devices() - get_nmb_of_close_devices()

def get_data():
    r = requests.get('https://api.github.com/events')
    logging.info("requests: %s", r.text)


class Exposure:  
    def __init__(self):
        self._running = True
        self.exp = lib.en_rx_service.ENRxService()
        # scan for all COVID-19 exposure notifications
        # self.scanner = BeaconScanner(callback,packet_filter=[ExposureNotificationFrame])

    def terminate(self):  
        self._running = False  
        # self.scanner.stop()

    def run(self):
        # self.scanner.start()
        while self._running:
            time.sleep(5) #Five second delay
            #logging.info("Scan test:")
            #lib.fingerprint.scan()
            
            scan_result = self.exp.scan(t=2)
            
            for beacon in scan_result:
                #logging.info("Scan result rpi : %s", beacon.rpi)
                #logging.info("Scan result rssi : %s", beacon.rssi)
                rssi_db[beacon.rpi].append(beacon.rssi)
                secondsSinceEpoch = time.time()
                lastTimestamp_db[beacon.rpi] = secondsSinceEpoch
                rssi_average_last_100_db[beacon.rpi] = calc_average_rssi(beacon.rpi)
                oldKey = getKeyForFirstTimestampOlderThan5Sec()
                if oldKey is not None:
                    deleteKeyInDbs(oldKey)
 
            #logging.info("Average rssi: %s", get_average_rssi())
            logging.info("Number of close devices: %s", get_nmb_of_close_devices())
            logging.info("Number of far devices: %s", get_nmb_of_far_devices())
            #logging.info("Devices: %s", get_local_devices())
            #logging.info("Join data: %s", join_data())
            #get_data()

app = Flask(__name__)

@app.route("/")
def main():
    # https://stackoverflow.com/questions/28207761/where-does-flask-look-for-image-files
    image_file = url_for('static', filename='smittestop_web.png')
    total_nmb = str(get_number_of_devices())
    close_nmb = str(get_nmb_of_close_devices())
    far_nmb = str(get_nmb_of_far_devices())

    logging.info("File: %s", image_file)
    return render_template('index.html', image_file=image_file, totalnumber=total_nmb,closenumber=close_nmb, farnumber=far_nmb)

@app.route("/localdevices")
def local_devices():
    #myLocal = str(get_local_devices())
    return get_local_devices()

if __name__ == "__main__":

    logging.info("Exposure Tracker:")
    if "SENSORS" in os.environ:
        sensors_selected = os.environ["SENSORS"]
        logging.info("Sensors: %s", sensors_selected)

    #Create Class
    Exposure = Exposure()
    
    #Create Thread
    ExposureThread = Thread(target=Exposure.run)
    #Start Thread 
    ExposureThread.start()
    
    if not local:
        #Create Thread
        ServerThread = Thread(target=app.run(host='0.0.0.0', port=80))
        #Start Thread 
        ServerThread.start()