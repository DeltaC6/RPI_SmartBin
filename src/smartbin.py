import RPi.GPIO as GPIO
import serial

import time
import threading

class SmartBin:
    def __init__(self):
        print('[INFO] Initializing components.')
        # Constants
        self.LED_PIN = 16
        self.TRIG_PIN = 20
        self.ECHO_PIN = 21
        self.SERIAL_PORT = '/dev/ttyS0'
        self.BIN_DEPTH = 90     # unit is in cm

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
            self.ser = serial.Serial(self.SERIAL_PORT, 115200)
        except Exception as e:
            print('[ERROR] Could not open serial.')
            print(e)
            self.ser.close()
            self.isRunning = False
        
    def blink(self):
        self.t = threading.Timer(1.0, self.blink)
        self.t.setName('blinker')
        self.ledState = not self.ledState
        GPIO.output(self.LED_PIN, self.ledState)
        self.t.start()

    def run(self):
        try:
            print('[INFO] Running application')
            while self.isRunning:
                # Acquiring device locaiotn and status
                self.getLocaiton()
                #self.getStatus()
                print('[INFO] DATA: {}, {}, {}'.format(self.lat, self.lng, self.status))

                # Sending data to server

                # Delay
                time.sleep(5.0)
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
            depth = round(deltaT * (34300 / 2.0), 2)    # Currnet depth of bin
            self.status = (1.0 - (depth / self.BIN_DEPTH)) * 100.0
        except Exception as e:
            print('[ERROR] Failed to acquire bin status.')
            print(e)

    def close(self):
        print('[INFO] Closing application')
        self.isRunning = False  # Closing current thread.
        self.t.cancel()         # Closing blinker thread.
        self.ser.close()        # Closing serial.
        GPIO.cleanup()          # Closng GPIO

