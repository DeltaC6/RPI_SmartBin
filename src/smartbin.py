################################################################################
##
# @author   Syed Asad Amin
# @date     Dec 1st, 2020
# @file     smartbin.py
# @version  v1.0.0
#               | v1.0.0 -> Added the smartbin class.
#                           Integrated the GPS and ultrasonic sensors.
#                           Added Ubidots request functions.
#               | v1.0.1 -> Added the API for server communication.
#
# @note     This is a program written in python to implement Smart Bin project.
#           
#           This project uses a GPS module and an ultrasonic module to get 
#           locaiton and status of the BIN respectively.
################################################################################

import RPi.GPIO as GPIO
import serial

import json
import socket
import time
import threading

class SmartBin:
    HOST = 'industrial.api.ubidots.com'
    PORT = 80

    SERIAL_PORT = '/dev/ttyS0'
    SERIAL_BAUD = 115200

    LED_PIN = 21
    TRIG_PIN = 16
    ECHO_PIN = 20

    BIN_DEPTH = 90

    def __init__(self):
        print('[INFO] Initializing components.')
        # Variables
        self.isRunning = True
        self.ledState = False
        self.lat = 0.0              # This is the current latitude of BIN
        self.lng = 0.0              # This is the current longitide of BIN
        self.status = 0.0           # This is the filled status of BIN in %

        # Initializations
        self.InitGPIO()
        self.InitSerial()

    def InitGPIO(self):
        try:
            GPIO.setmode(GPIO.BCM)                  # BCM config

            GPIO.setup(self.LED_PIN, GPIO.OUT)      # LED as output
            GPIO.setup(self.TRIG_PIN, GPIO.OUT)     # TRIG as output
            GPIO.setup(self.ECHO_PIN, GPIO.IN)      # ECHO as input

            GPIO.output(self.LED_PIN, self.ledState)
            GPIO.output(self.TRIG_PIN, GPIO.LOW)

            self.blink()
        except Exception as e:
            print('[ERROR] Could not config gpio')
            print(e)
            GPIO.cleanup()
            self.isRunning = False

    def InitSerial(self):
        try:
            self.ser = serial.Serial(self.SERIAL_PORT, self.SERIAL_BAUD)
        except Exception as e:
            print('[ERROR] Could not open serial.')
            print(e)
            self.ser.close()
            self.isRunning = False
        
    def blink(self):
        try:
            self.t = threading.Timer(1.0, self.blink)
            self.t.setName('blinker')
            self.ledState = not self.ledState
            GPIO.output(self.LED_PIN, self.ledState)
            self.t.start()
        except Exception as e:
            print('[ERROR] Blinker thread error.')
            print(e)

    def run(self):
        try:
            print('[INFO] Running application')
            while self.isRunning:
                # Acquiring device locaiotn and status
                self.getLocaiton()
                self.getStatus()
                print('[INFO] DATA: {}, {}, {}'.format(self.lat, self.lng, self.status))

                # Sending data to server
                self.uploadData()

                # Delay
                time.sleep(10.0)
        except KeyboardInterrupt:
            print('[WARN] Force colsed application')
            self.isRunning = False

    def getLocaiton(self):
        try:
            data = self.ser.readline()
            packets = data.split('\n')
            for packet in packets:
                if '$GPRMC' in packet:
                    contents = packet.split(',')
                    rawlat = float(contents[3])
                    rawlng = float(contents[5])
                    self.lat = self.__convertRaw(rawlat)
                    self.lng = self.__convertRaw(rawlng)
                else:
                    continue
        except Exception as e:
            print('[ERROR] Failed to acquire GPS location.')
            print(e)

    def __convertRaw(self, val):
        a = int(val / 100)
        b = val - (a * 100)
        return a + (b / 60)

    def getStatus(self):
        try:
            GPIO.output(self.TRIG_PIN, GPIO.HIGH)
            time.sleep(0.00001)     # 10us pulse
            GPIO.output(self.TRIG_PIN, GPIO.LOW)

            while GPIO.input(self.ECHO_PIN) == 0:
                startTime = time.time()

            while GPIO.input(self.ECHO_PIN) == 1:
                stopTime = time.time()

            deltaT = stopTime - startTime
            depth = round(deltaT * (34300 / 2.0), 2)
            self.status = (1.0 - (depth / self.BIN_DEPTH)) * 100.0
        except Exception as e:
            print('[ERROR] Failed to acquire bin status.')
            print(e)

    def uploadData(self):
        jsonStr = self.createJson()
        postStr = self.createPacket(jsonStr)
        self.sendData(postStr)

    def createJson(self):
        timestamp = int(time.time() * 1000)
        msg = {
            "position": {
            "value": 1,
            "timestamp": timestamp,
                "context": {
                    "lat": self.lat,
                    "lng": self.lng
                }
            },
            "status": {
                "value": self.status,
                "timestamp": timestamp,
                "context": {
                    "lat": self.lat,
                    "lng": self.lng
                }
            }
        }
        return json.dumps(msg)
    
    def createPacket(self, data):
        DEVICE_LABEL = 'sb1'
        USER_AGENT = 'RPI/3'
        TOKEN = ''

        postStr = "POST /api/v1.6/devices/{} HTTP/1.1\r\n".format(DEVICE_LABEL)
        postStr += "Host: {}\r\n".format(self.HOST)
        postStr += "User-Agent: {}\r\n".format(USER_AGENT)
        postStr += "X-Auth-Token: {}\r\n".format(TOKEN)
        postStr += "Content-Type: application/json\r\n"
        postStr += "Content-Length: {}\r\n\r\n".format(len(data))
        postStr += data + "\r\n"
        return postStr

    def sendData(self, msg):
        try:
            serverAddress = (self.HOST, self.PORT)
            sendBuffer = msg.encode()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(serverAddress)
            s.sendall(sendBuffer)
            recvBuffer = s.recv(1024)
            recv = recvBuffer.decode()
            if '200 OK' in recv:
                print('[INFO] Data uploaded to server.')
            else:
                print('[ERROR] Could not upload data to server.')
                print(recv)
        except Exception as e:
            print('[ERROR] Server communication error.')
            print(e)

    def close(self):
        print('[INFO] Closing application')
        self.isRunning = False  # Closing current thread.
        self.t.cancel()         # Closing blinker thread.
        self.ser.close()        # Closing serial.
        GPIO.cleanup()          # Closng GPIO
