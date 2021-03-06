

__author__ = 'Aoyagi Knesuke'

import os
import atexit
import itertools
import math
import time
import pigpio

PORT = 18
FREQ = 2000
MAX_PWM_DUTY = 1000000
GRAD = 3
STEP = 0.0008
BASE_INTERVAL = 0.04
MAX_LAZY = 6
LAZY_GRAD = 8.2
MAX_LUM=100 * 10**4
MIN_LUM=  5 * 10**4
HEAT_TICK = 20
HEAT_DIVER = 100
ACCEL_START = 20
HEATER_GRAD= 1.0024
COOLER_CONST=       1 *10**-6
COOLER_MULTI= 1 + 425 *10**-3

# class Accumrator():
#     def __init__(self, slots={"x":0,"y":0}):
#         for name, initial in slots.items():
#             setattr(self, name, initial)

#     def add(*vals):

def abscrop(v, n):
    if v == 0:
        return 0
    elif v > 0:
        return max(n,v)
    else:
        return min(-n,v)

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
    

def pos(x, floor=0):
    return max(floor, x)
def around(x):
    return abs(round(x))
def sine(rad):
    return (math.cos(rad) + 1)**GRAD / 2**GRAD
def wave(rad):
    return around(sine(rad) * (MAX_LUM) + MIN_LUM)

def rescale(value):
    return pos(MAX_LAZY - math.log(value - MIN_LUM + 1, LAZY_GRAD), 1)
def lazy(value):
    return BASE_INTERVAL * rescale(value)


# TimeRange, Heat -> Heat
def cooldown(timerange, heat):
    return round(heat**COOLER_MULTI * timerange * COOLER_CONST)
# Luminance, TimeRange -> Heat
def heatup(lum_average, timerange):
    v = lum_average // HEAT_DIVER
    return round((v + math.log(MAX_LUM-v+1,HEATER_GRAD)) * timerange)
class HeatCounter():
    def __init__(self, heat=0, tick=HEAT_TICK):
        self.tick = tick
        self.heat = heat
        self.heatbuffer = 0
        self.reset()

    def count(self, lum, interval):
        self.accumrate(lum, interval)
        if self.overTick():
            self.update()
            self.reset()
    
    def accumrate(self, lum, interval):
        #self.sum_lum += pos(lum - MIN_LUM)
        self.sum_lum += pos(lum)
        self.sum_interval += interval
        self._count += 1
    def overTick(self):
        return self.sum_interval >= self.tick
    def update(self):
        heater = heatup(self.sum_lum//self._count, self.sum_interval)
        heat = heater + (self.heat*HEAT_DIVER)
        cooler = cooldown(self.sum_interval, heat)
        self.heat = pos(heat - cooler) // HEAT_DIVER
        print("heater=%s cooler=%s heat=%s heatbuffer=%s" % (heater,cooler,self.heat,self.heatbuffer))
        if not isinstance(self.heat, int):
            raise Exception("self.heat is not integral")
        setlast(getnow(), self.heat)
    def reset(self):
        self.sum_lum = self.sum_interval = self._count = 0
    def _addheat(self):
        self.heatbuffer += abscrop((self.heat - self.heatbuffer) // ACCEL_START, 1)        
    def getheat(self):
        self._addheat()
        return self.heatbuffer

pi = pigpio.pi()
atexit.register(pi.stop)

def change_lum(lightness):
    pi.hardware_PWM(PORT, FREQ, lightness)

atexit.register(change_lum, 0)

curve = (wave(x) for x in frange(-math.pi, math.pi, STEP))
#curve3 = flatrepeat(curve,3)
curveE = itertools.cycle(curve)

prev, heat = getlast()
heat_counter = HeatCounter(heat)
heat_counter.count(0, getnow() - prev)

print(heat_counter.heatbuffer, heat_counter.heat)
for i,v in enumerate(curveE):
    #interval = BASE_INTERVAL
    interval = lazy(v)
    time.sleep(interval)
    val = min(MAX_LUM, v + heat_counter.getheat())
    change_lum(val)
    heat_counter.count(val,interval)
    if i % 100 == 0:
        t = time.strftime("%H:%M:%S", time.localtime())
        print(v, val, t, interval)
