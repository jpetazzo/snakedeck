#!/usr/bin/env python3

import glob
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


    def inc(self, seconds):
        seconds = int(seconds)
        self.timestamp += seconds
        self.save()
    def dec(self, seconds):
        seconds = int(seconds)
        self.timestamp -= seconds
        self.save()


class CountdownManager(object):

    def __init__(self, directory="."):
        self.directory = directory
        if not os.path.isdir(directory):
            os.makedirs(directory)
        self.countdowns = {}

    def once(self):
        names = [ filename[:-3] for filename in glob.glob(os.path.join(self.directory, "*.ts")) ]
        for name in names:
            if name not in self.countdowns:
                self.countdowns[name] = Countdown(name, self.directory)
            self.countdowns[name].update()

    def loop(self):
        while True:
            self.once()
            time.sleep(1)

    def __getitem__(self, name):
        if name not in self.countdowns:
            self.countdowns[name] = Countdown(name, self.directory)
        return self.countdowns[name]


if __name__ == "__main__":
    if sys.argv[1] == "_":
        CountdownManager().loop()
    else:
        countdown = Countdown(sys.argv[2])        
        method = getattr(countdown, sys.argv[1])
        print(method(*sys.argv[3:]))


def snakedeck_plugin(directory):
    countdownManager = CountdownManager(directory)
    threading.Thread(target=countdownManager.loop).start()
    return countdownManager

