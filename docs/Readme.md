# Smart Bin Project - IoT Enabled via Raspberry Pi

## INTRODUCTION

This is an application written in python language to run on Raspberry Pi
platform. Raspberry Pi is a Single Board Computer (SBC) that runs Raspbian -
a Debian flavour of Linux officially provided by Raspberry Pi foundation.

This program uses a GPS module and an UltraSonic sensor to grab the location
and filled status of the SMART BIN.

This locaiton and status is then uploaded to an IoT enabled server called
ThingSpeak. Many various server are available as an IoT cloud and could have
been used with this application but for simplicity ThingSpeak server was chosen.

## DEPENDENCIES

Following program and packages are needed to be installed on Raspberry Pi beofre
using this applicaiton.

- [X] Python

``` bash
sudo apt-get install python-dev python3-dev
```

- [X] Libraries

``` bash
sudo pip install pyserial
sudo pip install RPi.GPIO
```

## USAGE

Use following command in terminal to run the application.

Goto /src folder then type in terminal

``` bash
sudo python main.py
```

## TODO

- Adding server communication methods.

## TESTING

- [X] GPS test complete
- [X] UltraSonic sensor test complete
- [ ] Server communication testing complete
