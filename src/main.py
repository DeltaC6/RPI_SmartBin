################################################################################
##
# @author   Syed Asad Amin
# @date     Dec 1st, 2020
# @version  v1.0.0
# @file     main.py
#
# @note     This is a program written in python to implement Smart Bin project.
#           
#           This project uses a GPS module and an ultrasonic module to get 
#           locaiton and status of the BIN respectively.
################################################################################

import os
import sys

from smartbin import SmartBin

def main():
    try:
        app = SmartBin()
        app.run()
    except Exception as e:
        print(e)
    finally:
        app.close()

if __name__ == "__main__":
    if not os.getegid() == 0:
        sys.exit('Start this application as root')
    main()
