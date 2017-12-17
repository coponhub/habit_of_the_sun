
__author__ = 'Aoyagi Knesuke'

import os
import atexit
import itertools
import math
import time
import pigpio

# class Accumrator():
#     def __init__(self, slots={"x":0,"y":0}):
#         for name, initial in slots.items():
#             setattr(self, name, initial)

#     def add(*vals):

def frange(start, stop, step):
    return itertools.takewhile(lambda x: x< stop, itertools.count(start, step))

def flatten(listOfLists):
    "Flatten one level of nesting"
    return itertools.chain.from_iterable(listOfLists)

def flatrepeat(iterator,n):
    return flatten(itertools.repeat(iterator,n))

def setlast(time, heat):
    with open("last_data", "w") as f:
        f.write(",".join(map(str, (time,heat))))

def getlast():
    try:
        with open("last_data") as f:
            t = f.read()
        return tuple(int(x) for x in t.split(","))
    
    except FileNotFoundError as e:
        return 0, 0

def getnow():
    return round(time.time())
    
MAX_PWM_DUTY = 1000000
BASE_INTERVAL = 0.04
step = 0.002
PORT = 18
FREQ = 2000
GRAD = 3
TIME_GRAD = 1.01
MAX_LUM=1000000
MIN_LUM=118000
LIFTER_LUM_DIFF = 10000
MIN_LUM_LIFT=30000
MIN_LUM_CEIL = MIN_LUM + MIN_LUM_LIFT
HEAT_TICK = 2

def pos(x):
    return max(0,x)
def around(x):
    return abs(round(x))
def sine(rad):
    return (math.cos(rad) + 1)**GRAD / 2**GRAD
def wave(rad):
    return around(sine(rad) * (MAX_LUM) + MIN_LUM)

def rescale(value):
    return pos(10 - math.log(value - MIN_LUM + 1, TIME_GRAD))
def lazy(value):
    return BASE_INTERVAL * rescale(value)

# TimeRange, Heat -> Heat
def cooldown(timerange, heat):
    return round(heat * timerange * 0.01)
# Luminance, TimeRange -> Heat
def heatup(lum_average, timerange):
    return round((lum_average // 100) * timerange)
class HeatCounter():
    def __init__(self, heat=0, tick=HEAT_TICK):
        self.tick = tick
        self.heat = heat
        self.reset()

    def count(self, lum, interval):
        self.accumrate(lum, interval)
        if self.overTick():
            self.update()
            self.reset()
    
    def accumrate(self, lum, interval):
        self.sum_lum += pos(lum - MIN_LUM)
        self.sum_interval += interval
        self._count += 1
    def overTick(self):
        return self.sum_interval >= self.tick
    def update(self):
        heater = heatup(self.sum_lum//self._count, self.sum_interval)
        heat = heater + self.heat
        cooler = cooldown(self.sum_interval, heat)
        self.heat = pos(heat - cooler)
        print("heater=%s cooler=%s self.heat=%s" % (heater,cooler,self.heat))
        if not isinstance(self.heat, int):
            raise Exception("self.heat not integral")
        setlast(getnow(), self.heat)
    def reset(self):
        self.sum_lum = self.sum_interval = self._count = 0

pi = pigpio.pi()
atexit.register(pi.stop)

def change_lum(lightness):
    pi.hardware_PWM(PORT, FREQ, lightness)

atexit.register(change_lum, 0)

curve = (wave(x) for x in frange(-math.pi, math.pi, step))
#curve3 = flatrepeat(curve,3)
curveE = itertools.cycle(curve)

prev, heat = getlast()
heat_counter = HeatCounter(heat)
heat_counter.count(0, getnow() - prev)

for i,v in enumerate(curveE):
    if i % 100 == 0:
        t = time.strftime("%H:%M:%S", time.localtime())
        print(v, t)
    #interval = lazy(v)
    interval = BASE_INTERVAL
    time.sleep(interval)
    change_lum(min(MAX_LUM, v + heat_counter.heat//100))
    heat_counter.count(v,interval)

