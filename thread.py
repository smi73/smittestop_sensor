from threading import Thread
from collections import defaultdict
import time
import lib.epd2in13_V1
from PIL import Image,ImageDraw,ImageFont
import traceback
import logging
import os
from beacontools import BeaconScanner, ExposureNotificationFrame
from beacontools import parse_packet

global rssi_db
global rssi_average_last_100_db
rssi_db = defaultdict(list)
global lastTimestamp_db
lastTimestamp_db = {}
rssi_average_last_100_db = {}

if "DEBUG" in os.environ:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


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
    j2 = [i for i in j if i >= -60.0]
    myLen = len(j2)
    return myLen

def get_nmb_of_far_devices():
    return get_number_of_devices() - get_nmb_of_close_devices()

class ExposureProgram:  
    def __init__(self):
        self._running = True
        # scan for all COVID-19 exposure notifications
        self.scanner = BeaconScanner(callback,packet_filter=[ExposureNotificationFrame])
        

    def terminate(self):  
        self._running = False  
        self.scanner.stop()

    def run(self):
        self.scanner.start()
        while self._running:
            time.sleep(5) #Five second delay
            #print(rssi_db.items())
            #print(lastTimestamp_db.items())
            print("Devices found: {}.".format(get_number_of_devices()))
            print("Average rssi: {}.".format(get_average_rssi()))
            print("close rssi: {}.".format(get_nmb_of_close_devices()))



class DrawProgram:  
    def __init__(self):
        self._running = True
        self.epd = lib.epd2in13_V1.EPD()
        self.epd.init(self.epd.lut_full_update)
        self.epd.Clear(0xFF)
        self.epd.init(self.epd.lut_partial_update)
        self.font24 = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 24)
        self.time_image = Image.new('1', (lib.epd2in13_v1.EPD_HEIGHT, lib.epd2in13_V1.EPD_WIDTH), 255)
        
        bmp = Image.open('smitte-stop-logo.bmp')
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
            DevicesAndTime = "<-:{} ->:{} @{}".format(get_nmb_of_close_devices(), get_nmb_of_far_devices(), myTime)  
            self.draw.text((20, 80), DevicesAndTime, font = self.font24, fill = 0)
            self.newimage = self.time_image.crop([10, 10, 120, 50])
            self.time_image.paste(self.newimage, (10,10))  
            self.epd.display(self.epd.getbuffer(self.time_image))
            self._count = self._count + 1
            if self._count == 50:
                self.epd.init(self.epd.lut_full_update)
                self.epd.Clear(0xFF)
                self.epd.init(self.epd.lut_partial_update)
                self._count = 0
            
            #print("Count: {}.".format(self._count))
            

                



logging.info("Exposure Tracker:")
#Create Class
Draw = DrawProgram()
#Create Thread
DrawThread = Thread(target=Draw.run) 
#Start Thread 
DrawThread.start()

#Create Class
#Exposure = ExposureProgram()

#Create Thread
#ExposureThread = Thread(target=Exposure.run) 

#Start Thread 
#ExposureThread.start()


print("Smitte-stop Tracer start: ")
# Exit = False #Exit flag
# while Exit==False:
#  cycle = cycle + 0.1 
#  print("Main Program increases cycle+0.1 - {}.".format(cycle))

#  time.sleep(1) #One second delay
#  if (cycle > 5): Exit = True #Exit Program

# Draw.terminate()
# Exposure.terminate()
# print("Goodbye :)")
