from threading import Thread
from flask import Flask, render_template, url_for
from collections import defaultdict
import time
import lib.epd2in13_V1
import lib.en_rx_service

from PIL import Image,ImageDraw,ImageFont
import traceback
import logging
import os
from beacontools import BeaconScanner, ExposureNotificationFrame
from beacontools import parse_packet




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
            #logging.info("Close rssi: %s", get_nmb_of_close_devices())

class Draw:  
    def __init__(self):
        self._running = True
        self.epd = lib.epd2in13_V1.EPD()
        self.epd.init(self.epd.lut_full_update)
        self.epd.Clear(0xFF)
        self.epd.init(self.epd.lut_partial_update)
        self.font24 = ImageFont.truetype(root_path + '/fonts/wqy-microhei.ttc', 24)
        self.wifi = ImageFont.truetype(root_path +'/fonts/WIFI.ttf', 28)
        self.time_image = Image.new('1', (lib.epd2in13_V1.EPD_HEIGHT, lib.epd2in13_V1.EPD_WIDTH), 255)
        
        bmp = Image.open(root_path + '/bitmaps/smitte-stop-logo_epaper.bmp')
        self.time_image.paste(bmp, (50,10))    
        self.epd.display(self.epd.getbuffer(self.time_image))
        time.sleep(2)
        self.draw = ImageDraw.Draw(self.time_image)
        self._count = 0
        
    def terminate(self):  
        self._running = False  
        self._count = 0

    def run(self):        
        while self._running:
            self.draw.rectangle((20, 80, 220, 105), fill = 255)
            myTime = time.strftime('%H:%M:%S')
            #logging.info("Time: %s", myTime)
            DevicesAndTime = " {}     {}       {}".format(get_nmb_of_close_devices(),  myTime, get_nmb_of_far_devices())  
            logging.info("Text: %s", DevicesAndTime)
            self.draw.text((20, 50), "B", font = self.wifi, fill = 0)
            self.draw.text((195, 50), "2", font = self.wifi, fill = 0)
            self.draw.text((22, 80), DevicesAndTime, font = self.font24, fill = 0)
            self.newimage = self.time_image.crop([10, 10, 120, 50])
            self.time_image.paste(self.newimage, (10,10))  
            self.epd.display(self.epd.getbuffer(self.time_image))
            self._count = self._count + 1
            if self._count == 50:
                #logging.info("Refresh Time: %s", myTime)
                self.epd.init(self.epd.lut_full_update)
                self.epd.Clear(0xFF)
                self.epd.init(self.epd.lut_partial_update)
                self._count = 0
            



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


if __name__ == "__main__":
    logging.info("Exposure Tracker:")
    #Create Class
    Draw = Draw()
    #Create Thread
    DrawThread = Thread(target=Draw.run)
    #Start Thread 
    DrawThread.start()
    
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