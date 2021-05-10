#!/usr/bin/env python3

import glob
import logging
import os
import sys
import threading
import time


class Countdown(object):
    
    def __init__(self, name, directory="."):
        
        self.name = name
        self.tsfile = os.path.join(directory, name + ".ts")
        self.txtfile = os.path.join(directory, name + ".txt")
        try:
            self.timestamp = int(float(open(self.tsfile).read()))
        except Exception as e:
            print("Couldn't read timestamp ({}), setting to now".format(e))
            self.timestamp = time.time()
    

    def init_hm(self, hour, minute):
        t = list(time.localtime())
        t[3] = int(hour)
        t[4] = int(minute)
        t[5] = 0
        t = tuple(t)
        self.timestamp = time.mktime(t)
        if self.timestamp < time.time():
            self.timestamp += 3600*24
        self.save()


    def init_s(self, seconds):
        seconds = int(seconds)
        self.timestamp = time.time() + seconds
        self.save()


    def save(self):
        with open(self.tsfile, "w") as f:
            f.write(str(self.timestamp))
        self.update()


    def fmt(self):
        delta = int(self.timestamp - time.time())
        if delta <= 0:
            return "--:--:--"
        return "{:02d}:{:02d}:{:02d}".format(
                delta//3600, delta//60 % 60, delta % 60)


    def update(self):
        with open(self.txtfile, "w") as f:
            f.write(self.fmt())


    def loop(self):
        while True:
            self.update()
            time.sleep(1)


    def inc(self, seconds):
        seconds = int(seconds)
        self.timestamp += seconds
        self.save()
    def dec(self, seconds):
        seconds = int(seconds)
        self.timestamp -= seconds
        self.save()


if __name__ == "__main__":
    if sys.argv[1] == "_":
        while True:
            for tsfile in glob.glob("*.ts"):
                basename = tsfile[:-3]
                countdown = Countdown(basename)
                countdown.update()
            time.sleep(1)


    countdown = Countdown(sys.argv[1])        
    method = getattr(countdown, sys.argv[2])
    print(method(*sys.argv[3:]))
else:
    # Used as a module, start the update loop in a thread
    countdowns = {}
    plugin_dir = os.path.dirname(__file__)
    for tsfile in glob.glob(os.path.join(plugin_dir, "*.ts")):
        logging.debug(f"Found countdown file {tsfile}.")
        basename = os.path.basename(tsfile)[:-3]
        countdown = Countdown(basename, plugin_dir)
        countdowns[basename] = countdown
        threading.Thread(target=countdown.loop).start()
